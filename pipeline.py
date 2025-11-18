"""
Main translation pipeline with BERT alignment
Orchestrates: Extraction → Translation → BERT Alignment → PPTX Update
"""

import logging
import time
from pathlib import Path
from typing import Optional

import config
from extract_content import ContentExtractor
from translate_paragraphs import ParagraphTranslator
from apply_alignment import AlignmentApplicator
from build_slide_context import SlideContextBuilder
from translate_content import ContentTranslator
from apply_table_alignment import TableAlignmentApplicator
from update_pptx import PowerPointUpdater

# Set up logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TranslationPipeline:
    """Main translation pipeline with BERT alignment."""

    def __init__(self, translator_type: Optional[str] = None, glossary: Optional['TerminologyGlossary'] = None):
        """
        Initialize translation pipeline.

        Args:
            translator_type: Type of translator to use ("local", "openai", "anthropic")
                           If None, uses config.TRANSLATOR_TYPE
            glossary: Optional TerminologyGlossary for consistent translations
        """
        self.translator_type = translator_type or config.TRANSLATOR_TYPE
        self.glossary = glossary
        logger.info(f"Initializing translation pipeline with {self.translator_type} translator")
        if glossary:
            logger.info(f"Glossary loaded with {len(glossary)} entries")

        # Initialize components
        self.extractor = ContentExtractor()
        self.translator = ParagraphTranslator(
            translator_type=self.translator_type,
            glossary=self.glossary
        )
        self.aligner = AlignmentApplicator(glossary=self.glossary)
        self.context_builder = SlideContextBuilder()

        # Reuse the same translator instance to save GPU memory
        # ParagraphTranslator and ContentTranslator can share the model
        self.content_translator = ContentTranslator(
            translator_type=self.translator_type,
            glossary=self.glossary,
            shared_translator=self.translator.translator  # Share the underlying translator
        )
        self.table_aligner = TableAlignmentApplicator(glossary=self.glossary)
        self.updater = PowerPointUpdater()

    def run(
        self,
        input_pptx: str,
        output_pptx: str,
        context: Optional[str] = None,
        keep_intermediate: bool = True
    ) -> dict:
        """
        Run the complete translation pipeline.

        Args:
            input_pptx: Path to input PowerPoint file
            output_pptx: Path to output PowerPoint file
            context: Optional context for translation (e.g., glossary terms)
            keep_intermediate: Whether to keep intermediate JSONL files

        Returns:
            Dictionary with pipeline statistics
        """
        start_time = time.time()
        logger.info("=" * 80)
        logger.info("Starting Translation Pipeline")
        logger.info(f"Input: {input_pptx}")
        logger.info(f"Output: {output_pptx}")
        logger.info(f"Translator: {self.translator_type}")
        logger.info("=" * 80)

        stats = {
            "input_file": input_pptx,
            "output_file": output_pptx,
            "translator_type": self.translator_type,
            "steps": {}
        }

        try:
            # Step 1: Extract content (text, tables, charts)
            logger.info("\n[Step 1/9] Extracting content from PowerPoint")
            step_start = time.time()

            extracted_text = str(config.EXTRACTED_PARAGRAPHS_JSONL)
            extracted_tables = str(config.TEMP_DIR / "extracted_tables.jsonl")
            extracted_charts = str(config.TEMP_DIR / "extracted_charts.jsonl")

            counts = self.extractor.extract_all(
                pptx_path=input_pptx,
                text_output=extracted_text,
                table_output=extracted_tables,
                chart_output=extracted_charts
            )
            para_count = counts['text_paragraphs']

            step_time = time.time() - step_start
            stats["steps"]["extraction"] = {
                "paragraphs": para_count,
                "tables": counts.get('tables', 0),
                "charts": counts.get('chart_titles', 0),
                "time_seconds": round(step_time, 2)
            }
            logger.info(f"✓ Extracted {para_count} paragraphs, {counts.get('tables', 0)} tables, {counts.get('chart_titles', 0)} charts in {step_time:.2f}s")

            # Step 2: Translate paragraphs
            logger.info("\n[Step 2/9] Translating paragraphs")
            step_start = time.time()

            translated_paragraphs = str(config.TRANSLATED_PARAGRAPHS_JSONL)
            trans_count = self.translator.translate_paragraphs(
                extracted_text, translated_paragraphs, context=context
            )

            step_time = time.time() - step_start
            stats["steps"]["translate_paragraphs"] = {
                "paragraphs": trans_count,
                "time_seconds": round(step_time, 2)
            }
            logger.info(f"✓ Translated {trans_count} paragraphs in {step_time:.2f}s")

            # Step 3: Apply BERT alignment to paragraphs
            logger.info("\n[Step 3/9] Applying BERT alignment to paragraphs")
            step_start = time.time()

            aligned_paragraphs = str(config.ALIGNED_RUNS_JSONL)
            align_count = self.aligner.apply_alignment(translated_paragraphs, aligned_paragraphs)

            step_time = time.time() - step_start
            stats["steps"]["align_paragraphs"] = {
                "paragraphs": align_count,
                "time_seconds": round(step_time, 2)
            }
            logger.info(f"✓ Aligned {align_count} paragraphs in {step_time:.2f}s")

            # Step 4: Build slide context
            logger.info("\n[Step 4/9] Building slide context")
            step_start = time.time()

            slide_context = str(config.TEMP_DIR / "slide_context.jsonl")
            context_count = self.context_builder.build_context(aligned_paragraphs, slide_context)

            step_time = time.time() - step_start
            stats["steps"]["build_context"] = {
                "slides": context_count,
                "time_seconds": round(step_time, 2)
            }
            logger.info(f"✓ Built context for {context_count} slides in {step_time:.2f}s")

            # Step 5: Translate charts
            logger.info("\n[Step 5/9] Translating charts")
            step_start = time.time()

            translated_charts = str(config.TEMP_DIR / "translated_charts.jsonl")
            if counts.get('chart_titles', 0) > 0:
                chart_count = self.content_translator.translate_charts(
                    extracted_charts, slide_context, translated_charts
                )
                logger.info(f"✓ Translated {chart_count} charts in {time.time() - step_start:.2f}s")
            else:
                chart_count = 0
                logger.info(f"⏭️  No charts to translate")

            step_time = time.time() - step_start
            stats["steps"]["translate_charts"] = {
                "charts": chart_count,
                "time_seconds": round(step_time, 2)
            }

            # Step 6: Translate tables
            logger.info("\n[Step 6/9] Translating tables")
            step_start = time.time()

            translated_tables = str(config.TEMP_DIR / "translated_tables.jsonl")
            if counts.get('tables', 0) > 0:
                table_count = self.content_translator.translate_tables(
                    extracted_tables, slide_context, translated_tables
                )
                logger.info(f"✓ Translated {table_count} tables in {time.time() - step_start:.2f}s")
            else:
                table_count = 0
                logger.info(f"⏭️  No tables to translate")

            step_time = time.time() - step_start
            stats["steps"]["translate_tables"] = {
                "tables": table_count,
                "time_seconds": round(step_time, 2)
            }

            # Step 7: Apply BERT alignment to tables
            logger.info("\n[Step 7/9] Applying BERT alignment to tables")
            step_start = time.time()

            aligned_tables = str(config.TEMP_DIR / "aligned_tables.jsonl")
            if counts.get('tables', 0) > 0:
                table_align_count = self.table_aligner.apply_table_alignment(
                    translated_tables, aligned_tables
                )
                logger.info(f"✓ Aligned {table_align_count} tables in {time.time() - step_start:.2f}s")
            else:
                table_align_count = 0
                logger.info(f"⏭️  No tables to align")

            step_time = time.time() - step_start
            stats["steps"]["align_tables"] = {
                "tables": table_align_count,
                "time_seconds": round(step_time, 2)
            }

            # Step 8: Merge all translated content
            logger.info("\n[Step 8/9] Merging all translated content")
            step_start = time.time()

            merged_content = str(config.TEMP_DIR / "merged_content.jsonl")
            with open(merged_content, 'w', encoding='utf-8') as f_out:
                # Add aligned paragraphs
                if Path(aligned_paragraphs).exists():
                    with open(aligned_paragraphs, 'r', encoding='utf-8') as f_in:
                        for line in f_in:
                            f_out.write(line)

                # Add aligned tables
                if Path(aligned_tables).exists():
                    with open(aligned_tables, 'r', encoding='utf-8') as f_in:
                        for line in f_in:
                            f_out.write(line)

                # Add translated charts
                if Path(translated_charts).exists():
                    with open(translated_charts, 'r', encoding='utf-8') as f_in:
                        for line in f_in:
                            f_out.write(line)

            step_time = time.time() - step_start
            stats["steps"]["merge_content"] = {
                "time_seconds": round(step_time, 2)
            }
            logger.info(f"✓ Merged content in {step_time:.2f}s")

            # Step 9: Update PowerPoint
            logger.info("\n[Step 9/9] Updating PowerPoint presentation")
            step_start = time.time()

            update_counts = self.updater.update_presentation(
                input_pptx, merged_content, output_pptx
            )

            step_time = time.time() - step_start
            stats["steps"]["update_pptx"] = {
                "paragraphs": update_counts.get('paragraphs', 0),
                "tables": update_counts.get('tables', 0),
                "charts": update_counts.get('charts', 0),
                "time_seconds": round(step_time, 2)
            }
            logger.info(f"✓ Updated {update_counts.get('paragraphs', 0)} paragraphs, {update_counts.get('tables', 0)} tables, {update_counts.get('charts', 0)} charts in {step_time:.2f}s")

            # Clean up intermediate files if requested
            if not keep_intermediate:
                logger.info("\nCleaning up intermediate files")
                for file in [extracted_text, extracted_tables, extracted_charts,
                           translated_paragraphs, aligned_paragraphs, slide_context,
                           translated_charts, translated_tables, aligned_tables,
                           merged_content]:
                    try:
                        Path(file).unlink()
                    except:
                        pass

            # Calculate total time
            total_time = time.time() - start_time
            stats["total_time_seconds"] = round(total_time, 2)

            logger.info("\n" + "=" * 80)
            logger.info("Pipeline completed successfully!")
            logger.info(f"Total time: {total_time:.2f}s")
            logger.info(f"Output saved to: {output_pptx}")
            logger.info("=" * 80)

            return stats

        except Exception as e:
            logger.error(f"\n!!! Pipeline failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise


def main():
    """Command-line interface for translation pipeline."""
    import argparse

    parser = argparse.ArgumentParser(description="PowerPoint Translation Pipeline with BERT Alignment")
    parser.add_argument("input", help="Input PowerPoint file (.pptx)")
    parser.add_argument("output", help="Output PowerPoint file (.pptx)")
    parser.add_argument(
        "--translator",
        choices=["local", "openai", "anthropic"],
        default=None,
        help="Translator type (default: from config)"
    )
    parser.add_argument(
        "--context",
        help="Optional context for translation (e.g., glossary terms)"
    )
    parser.add_argument(
        "--no-keep-intermediate",
        action="store_false",
        dest="keep_intermediate",
        help="Delete intermediate JSONL files after completion"
    )
    parser.set_defaults(keep_intermediate=True)
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Set verbose logging if requested
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run pipeline
    pipeline = TranslationPipeline(translator_type=args.translator)
    stats = pipeline.run(
        input_pptx=args.input,
        output_pptx=args.output,
        context=args.context,
        keep_intermediate=args.keep_intermediate
    )

    # Print summary
    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)
    print(f"Input:       {stats['input_file']}")
    print(f"Output:      {stats['output_file']}")
    print(f"Translator:  {stats['translator_type']}")
    print(f"Total time:  {stats['total_time_seconds']}s")
    print("\nSteps:")
    for step_name, step_stats in stats["steps"].items():
        print(f"  {step_name:12s}: {step_stats['paragraphs']:3d} paragraphs in {step_stats['time_seconds']:6.2f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
