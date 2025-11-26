"""
Apply LLM-based alignment to redistribute formatting from source to target runs

This is an experimental alternative to BERT alignment that uses LLM to map
formatted terms to their translations.
"""

import json
import logging
from typing import Optional
from pathlib import Path
import config
from llm_formatting_aligner import LLMFormattingAligner
from translators import LocalLLMTranslator, OpenAITranslator, AnthropicTranslator

logger = logging.getLogger(__name__)


class LLMAlignmentApplicator:
    """Apply LLM-based alignment to translated paragraphs."""

    def __init__(
        self,
        translator_type: Optional[str] = None,
        translator: Optional[any] = None
    ):
        """
        Initialize LLM alignment applicator.

        Args:
            translator_type: Type of translator ("local", "openai", "anthropic")
                           If None, uses config.TRANSLATOR_TYPE
            translator: Existing translator instance to reuse (recommended to save GPU memory)
                       If provided, translator_type is ignored
        """
        # If translator instance is provided, use it directly (shared translator)
        if translator is not None:
            logger.info(f"Reusing existing translator instance (shared mode)")
            self.translator = translator
            # Still need to create the aligner with the shared translator
            self.aligner = LLMFormattingAligner(translator=self.translator)
            return

        # Otherwise, create a new translator
        translator_type = translator_type or config.TRANSLATOR_TYPE
        logger.info(f"Initializing LLM aligner with {translator_type} translator")

        # Initialize translator
        if translator_type == "local" or translator_type == "local-14b":
            if LocalLLMTranslator is None:
                raise RuntimeError(
                    "Local LLM translator not available. "
                    "Use translator_type='openai' or 'anthropic' instead."
                )

            model_name = config.LOCAL_MODEL_14B_NAME if translator_type == "local-14b" else config.LOCAL_MODEL_NAME
            logger.info(f"Using local model: {model_name}")

            self.translator = LocalLLMTranslator(
                model_name=model_name,
                source_lang=config.SOURCE_LANGUAGE,
                target_lang=config.TARGET_LANGUAGE,
                device=config.LOCAL_DEVICE,
                temperature=config.LOCAL_TEMPERATURE,
                max_tokens=config.LOCAL_MAX_TOKENS
            )
        elif translator_type == "openai":
            if not config.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not set in config or environment")
            self.translator = OpenAITranslator(
                api_key=config.OPENAI_API_KEY,
                model=config.OPENAI_MODEL,
                source_lang=config.SOURCE_LANGUAGE,
                target_lang=config.TARGET_LANGUAGE,
                temperature=config.OPENAI_TEMPERATURE,
                max_tokens=config.OPENAI_MAX_TOKENS
            )
        elif translator_type == "anthropic":
            if not config.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not set in config or environment")
            self.translator = AnthropicTranslator(
                api_key=config.ANTHROPIC_API_KEY,
                model=config.ANTHROPIC_MODEL,
                source_lang=config.SOURCE_LANGUAGE,
                target_lang=config.TARGET_LANGUAGE,
                temperature=config.ANTHROPIC_TEMPERATURE,
                max_tokens=config.ANTHROPIC_MAX_TOKENS
            )
        else:
            raise ValueError(f"Unknown translator type: {translator_type}")

        # Initialize LLM aligner with translator
        self.aligner = LLMFormattingAligner(translator=self.translator)

    def apply_alignment(
        self,
        translated_jsonl: str,
        output_jsonl: str,
        debug_jsonl: Optional[str] = None
    ) -> int:
        """
        Apply LLM alignment to redistribute formatting.

        Args:
            translated_jsonl: Path to translated paragraphs JSONL
            output_jsonl: Path to output JSONL with aligned runs
            debug_jsonl: Optional path to write detailed alignment debug info

        Returns:
            Number of paragraphs processed
        """
        logger.info(f"Applying LLM alignment to {translated_jsonl}")

        processed_count = 0
        Path(output_jsonl).parent.mkdir(parents=True, exist_ok=True)

        # Determine debug file path
        if debug_jsonl is None:
            output_path = Path(output_jsonl)
            debug_jsonl = str(output_path.parent / f"{output_path.stem}_debug{output_path.suffix}")

        Path(debug_jsonl).parent.mkdir(parents=True, exist_ok=True)

        with open(translated_jsonl, 'r', encoding='utf-8') as f_in, \
             open(output_jsonl, 'w', encoding='utf-8') as f_out, \
             open(debug_jsonl, 'w', encoding='utf-8') as f_debug:

            for line_num, line in enumerate(f_in, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    paragraph = json.loads(line)

                    # Get source and target text
                    src_text = paragraph["text"]
                    tgt_text = paragraph.get("translated_text", "")

                    if not src_text.strip() or not tgt_text.strip():
                        # Empty text, keep original runs
                        paragraph["aligned_runs"] = paragraph["runs"]
                        f_out.write(json.dumps(paragraph, ensure_ascii=False) + '\n')
                        continue

                    # Get source runs
                    src_runs = paragraph["runs"]

                    # Apply LLM alignment
                    logger.info(f"Aligning paragraph {line_num} with LLM")
                    logger.debug(f"Source: {src_text[:50]}...")
                    logger.debug(f"Target: {tgt_text[:50]}...")
                    logger.debug(f"Source runs: {len(src_runs)}")

                    aligned_runs, debug_info = self.aligner.align_paragraph_runs(
                        src_text=src_text,
                        tgt_text=tgt_text,
                        runs=src_runs,
                        source_lang=config.SOURCE_LANGUAGE,
                        target_lang=config.TARGET_LANGUAGE
                    )

                    # Add aligned runs to paragraph data
                    paragraph["aligned_runs"] = aligned_runs

                    # Add alignment metadata for debugging
                    paragraph["alignment_metadata"] = {
                        "alignment_method": "llm",
                        "source_runs_count": len(src_runs),
                        "aligned_runs_count": len(aligned_runs),
                        "source_text": src_text,
                        "target_text": tgt_text
                    }

                    # Write to output
                    f_out.write(json.dumps(paragraph, ensure_ascii=False) + '\n')
                    processed_count += 1

                    # Write detailed debug info to separate file
                    if debug_info:
                        debug_entry = {
                            "slide_index": paragraph.get("slide_index"),
                            "shape_index": paragraph.get("shape_index"),
                            "paragraph_index": paragraph.get("paragraph_index"),
                            "source_text": src_text,
                            "target_text": tgt_text,
                            "source_runs": src_runs,
                            "alignment_debug": debug_info
                        }
                        f_debug.write(json.dumps(debug_entry, ensure_ascii=False) + '\n')

                    logger.debug(f"Created {len(aligned_runs)} aligned runs from {len(src_runs)} source runs")

                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON at line {line_num}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error aligning paragraph at line {line_num}: {e}")
                    logger.exception("Full traceback:")
                    # Write paragraph with original runs on error
                    try:
                        paragraph["aligned_runs"] = paragraph["runs"]
                        f_out.write(json.dumps(paragraph, ensure_ascii=False) + '\n')
                    except:
                        pass
                    continue

        logger.info(f"Processed {processed_count} paragraphs to {output_jsonl}")
        logger.info(f"Debug alignment details written to {debug_jsonl}")
        return processed_count


def main():
    """Example usage."""
    import sys

    if len(sys.argv) < 3:
        print("Usage: python apply_llm_alignment.py <translated.jsonl> <aligned.jsonl> [translator_type]")
        print("\nTranslator types: local, openai, anthropic")
        print("\nExample:")
        print("  python apply_llm_alignment.py temp/translated_paragraphs.jsonl temp/aligned_runs_llm.jsonl openai")
        sys.exit(1)

    translator_type = sys.argv[3] if len(sys.argv) > 3 else None
    applicator = LLMAlignmentApplicator(translator_type=translator_type)
    count = applicator.apply_alignment(sys.argv[1], sys.argv[2])
    print(f"Aligned {count} paragraphs using LLM")


if __name__ == "__main__":
    main()
