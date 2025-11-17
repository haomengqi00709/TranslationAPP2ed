"""
Comprehensive test workflow for table and chart translation pipeline

This script tests each component step-by-step so you can verify:
1. Content extraction (text, tables, charts)
2. Paragraph translation and BERT alignment
3. Slide context building
4. Chart and table translation with context
5. PowerPoint update

Run with: python test_workflow.py
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import your modules
from extract_content import ContentExtractor
from translate_paragraphs import ParagraphTranslator
from apply_alignment import AlignmentApplicator
from build_slide_context import SlideContextBuilder
from translate_content import ContentTranslator
from update_pptx import PowerPointUpdater


def print_separator(title):
    """Print a nice separator."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def peek_jsonl(file_path, num_lines=2):
    """Show first few lines of a JSONL file."""
    logger.info(f"\n📄 Peeking at {file_path}:")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= num_lines:
                    break
                data = json.loads(line.strip())
                print(f"\n  Line {i+1}:")
                # Print condensed version
                if data.get("content_type") == "table":
                    print(f"    Type: table")
                    print(f"    Slide: {data.get('slide_index')}, Shape: {data.get('shape_index')}")
                    print(f"    Size: {data.get('rows')}x{data.get('cols')}")
                    print(f"    Cells: {len(data.get('cells', []))}")
                elif data.get("content_type") == "chart":
                    print(f"    Type: chart")
                    print(f"    Slide: {data.get('slide_index')}, Shape: {data.get('shape_index')}")
                    print(f"    Chart type: {data.get('chart_type')}")
                    if data.get('title'):
                        print(f"    Title: {data['title'].get('text', 'N/A')}")
                elif data.get("content_type") == "text" or data.get("text"):
                    print(f"    Type: text paragraph")
                    print(f"    Slide: {data.get('slide_index')}, Shape: {data.get('shape_index')}")
                    print(f"    Text: {data.get('text', '')[:60]}...")
                    print(f"    Runs: {len(data.get('runs', []))}")
                else:
                    # Slide context or other
                    print(f"    Keys: {list(data.keys())[:5]}...")
    except Exception as e:
        logger.error(f"Error peeking at file: {e}")


def test_complete_workflow():
    """Test the complete workflow step by step."""

    # Configuration
    INPUT_PPTX = "slides/PPT-3-Government-in-Canada1 (2).pptx"
    TEMP_DIR = Path("temp")
    OUTPUT_DIR = Path("output")

    # Ensure directories exist
    TEMP_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    # File paths
    extracted_text = TEMP_DIR / "extracted_text.jsonl"
    extracted_tables = TEMP_DIR / "extracted_tables.jsonl"
    extracted_charts = TEMP_DIR / "extracted_charts.jsonl"
    translated_paragraphs = TEMP_DIR / "translated_paragraphs.jsonl"
    aligned_paragraphs = TEMP_DIR / "aligned_paragraphs.jsonl"
    slide_context = TEMP_DIR / "slide_context.jsonl"
    translated_tables = TEMP_DIR / "translated_tables.jsonl"
    translated_charts = TEMP_DIR / "translated_charts.jsonl"
    output_pptx = OUTPUT_DIR / "test_workflow_output.pptx"

    print_separator("TESTING TABLE & CHART TRANSLATION WORKFLOW")
    print(f"\n📂 Input: {INPUT_PPTX}")
    print(f"📂 Output: {output_pptx}")
    print(f"📂 Temp files: {TEMP_DIR}/")

    # ========================================================================
    # STEP 1: Extract Content (Text, Tables, Charts)
    # ========================================================================
    print_separator("STEP 1: Extract Content")

    try:
        extractor = ContentExtractor()
        counts = extractor.extract_all(
            pptx_path=INPUT_PPTX,
            text_output=str(extracted_text),
            table_output=str(extracted_tables),
            chart_output=str(extracted_charts)
        )

        logger.info(f"✅ Extraction complete:")
        logger.info(f"   - {counts['text_paragraphs']} text paragraphs")
        logger.info(f"   - {counts['tables']} tables")
        logger.info(f"   - {counts['chart_titles']} charts")

        # Show samples
        if counts['text_paragraphs'] > 0:
            peek_jsonl(extracted_text, 1)
        if counts['tables'] > 0:
            peek_jsonl(extracted_tables, 1)
        if counts['chart_titles'] > 0:
            peek_jsonl(extracted_charts, 1)

    except Exception as e:
        logger.error(f"❌ Step 1 failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # ========================================================================
    # STEP 2: Translate Paragraphs
    # ========================================================================
    print_separator("STEP 2: Translate Paragraphs")

    try:
        translator = ParagraphTranslator(translator_type="local")
        para_count = translator.translate_paragraphs(
            input_jsonl=str(extracted_text),
            output_jsonl=str(translated_paragraphs)
        )

        logger.info(f"✅ Translated {para_count} paragraphs")
        peek_jsonl(translated_paragraphs, 1)

    except Exception as e:
        logger.error(f"❌ Step 2 failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # ========================================================================
    # STEP 3: Apply BERT Alignment to Paragraphs
    # ========================================================================
    print_separator("STEP 3: Apply BERT Alignment to Paragraphs")

    try:
        aligner = AlignmentApplicator()
        align_count = aligner.apply_alignment(
            translated_jsonl=str(translated_paragraphs),
            output_jsonl=str(aligned_paragraphs)
        )

        logger.info(f"✅ Aligned {align_count} paragraphs")
        peek_jsonl(aligned_paragraphs, 1)

    except Exception as e:
        logger.error(f"❌ Step 3 failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # ========================================================================
    # STEP 4: Build Slide Context
    # ========================================================================
    print_separator("STEP 4: Build Slide Context")

    try:
        context_builder = SlideContextBuilder()
        slide_count = context_builder.build_context(
            aligned_paragraphs_jsonl=str(aligned_paragraphs),
            output_jsonl=str(slide_context)
        )

        logger.info(f"✅ Built context for {slide_count} slides")
        peek_jsonl(slide_context, 1)

    except Exception as e:
        logger.error(f"❌ Step 4 failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # ========================================================================
    # STEP 5: Translate Charts (with slide context)
    # ========================================================================
    print_separator("STEP 5: Translate Charts")

    try:
        content_translator = ContentTranslator(translator_type="local")

        if counts['chart_titles'] > 0:
            chart_count = content_translator.translate_charts(
                charts_jsonl=str(extracted_charts),
                slide_context_jsonl=str(slide_context),
                output_jsonl=str(translated_charts)
            )
            logger.info(f"✅ Translated {chart_count} charts")
            peek_jsonl(translated_charts, 1)
        else:
            logger.info("⏭️  No charts to translate")

    except Exception as e:
        logger.error(f"❌ Step 5 failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # ========================================================================
    # STEP 6: Translate Tables (with slide context)
    # ========================================================================
    print_separator("STEP 6: Translate Tables")

    try:
        if counts['tables'] > 0:
            table_count = content_translator.translate_tables(
                tables_jsonl=str(extracted_tables),
                slide_context_jsonl=str(slide_context),
                output_jsonl=str(translated_tables)
            )
            logger.info(f"✅ Translated {table_count} tables")
            peek_jsonl(translated_tables, 1)
        else:
            logger.info("⏭️  No tables to translate")

    except Exception as e:
        logger.error(f"❌ Step 6 failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # ========================================================================
    # STEP 7: Merge All Content and Update PowerPoint
    # ========================================================================
    print_separator("STEP 7: Update PowerPoint with Translated Content")

    try:
        # Merge all translated content into one JSONL file
        merged_content = TEMP_DIR / "merged_content.jsonl"

        logger.info("Merging translated content...")
        with open(merged_content, 'w', encoding='utf-8') as f_out:
            # Add aligned paragraphs
            if aligned_paragraphs.exists():
                with open(aligned_paragraphs, 'r', encoding='utf-8') as f_in:
                    for line in f_in:
                        f_out.write(line)

            # Add translated tables
            if translated_tables.exists():
                with open(translated_tables, 'r', encoding='utf-8') as f_in:
                    for line in f_in:
                        f_out.write(line)

            # Add translated charts
            if translated_charts.exists():
                with open(translated_charts, 'r', encoding='utf-8') as f_in:
                    for line in f_in:
                        f_out.write(line)

        logger.info(f"✅ Merged content saved to {merged_content}")

        # Update PowerPoint
        updater = PowerPointUpdater()
        update_counts = updater.update_presentation(
            input_pptx=INPUT_PPTX,
            aligned_jsonl=str(merged_content),
            output_pptx=str(output_pptx)
        )

        logger.info(f"✅ PowerPoint updated:")
        logger.info(f"   - {update_counts['paragraphs']} paragraphs")
        logger.info(f"   - {update_counts['tables']} tables")
        logger.info(f"   - {update_counts['charts']} charts")

    except Exception as e:
        logger.error(f"❌ Step 7 failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print_separator("✅ WORKFLOW COMPLETE!")

    print(f"""
📊 Summary:
   Extracted:  {counts['text_paragraphs']} paragraphs, {counts['tables']} tables, {counts['chart_titles']} charts
   Translated: {para_count} paragraphs, {table_count if counts['tables'] > 0 else 0} tables, {chart_count if counts['chart_titles'] > 0 else 0} charts
   Updated:    {update_counts['paragraphs']} paragraphs, {update_counts['tables']} tables, {update_counts['charts']} charts

📂 Output saved to: {output_pptx}

🔍 Intermediate files in temp/:
   - {extracted_text.name}
   - {extracted_tables.name}
   - {extracted_charts.name}
   - {translated_paragraphs.name}
   - {aligned_paragraphs.name}
   - {slide_context.name}
   - {translated_tables.name}
   - {translated_charts.name}
   - {merged_content.name}

💡 Next steps:
   1. Open {output_pptx} to verify the translation
   2. Compare with original {INPUT_PPTX}
   3. Check if formatting is preserved in paragraphs
   4. Note: Tables don't have BERT alignment yet (single-run translation)
""")


if __name__ == "__main__":
    test_complete_workflow()
