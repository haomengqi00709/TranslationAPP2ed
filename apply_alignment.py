"""
Apply BERT alignment to redistribute formatting from source to target runs
"""

import json
import logging
from typing import Optional, TYPE_CHECKING
from pathlib import Path
import config
from bert_alignment import PowerPointBERTAligner

if TYPE_CHECKING:
    from glossary import TerminologyGlossary

logger = logging.getLogger(__name__)


class AlignmentApplicator:
    """Apply BERT alignment to translated paragraphs."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        max_phrase_length: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        glossary: Optional['TerminologyGlossary'] = None
    ):
        """
        Initialize alignment applicator.

        Args:
            model_name: BERT model name (defaults to config.BERT_MODEL_NAME)
            device: Device to use (defaults to config.BERT_DEVICE)
            max_phrase_length: Max phrase length (defaults to config.BERT_MAX_PHRASE_LENGTH)
            similarity_threshold: Similarity threshold (defaults to config.BERT_SIMILARITY_THRESHOLD)
            glossary: Optional terminology glossary for enhanced alignment
        """
        model_name = model_name or config.BERT_MODEL_NAME
        device = device or config.BERT_DEVICE
        max_phrase_length = max_phrase_length or config.BERT_MAX_PHRASE_LENGTH
        similarity_threshold = similarity_threshold or config.BERT_SIMILARITY_THRESHOLD

        logger.info("Initializing BERT aligner")
        self.aligner = PowerPointBERTAligner(
            model_name=model_name,
            device=device,
            max_phrase_length=max_phrase_length,
            similarity_threshold=similarity_threshold,
            glossary=glossary
        )

    def apply_alignment(
        self,
        translated_jsonl: str,
        output_jsonl: str,
        debug_jsonl: Optional[str] = None
    ) -> int:
        """
        Apply BERT alignment to redistribute formatting.

        Args:
            translated_jsonl: Path to translated paragraphs JSONL
            output_jsonl: Path to output JSONL with aligned runs
            debug_jsonl: Optional path to write detailed alignment debug info

        Returns:
            Number of paragraphs processed
        """
        logger.info(f"Applying BERT alignment to {translated_jsonl}")

        processed_count = 0
        Path(output_jsonl).parent.mkdir(parents=True, exist_ok=True)

        # Determine debug file path
        if debug_jsonl is None:
            # Default: same directory as output, with _debug suffix
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

                    # Apply BERT alignment
                    logger.info(f"Aligning paragraph {line_num}")
                    logger.debug(f"Source: {src_text[:50]}...")
                    logger.debug(f"Target: {tgt_text[:50]}...")
                    logger.debug(f"Source runs: {len(src_runs)}")

                    aligned_runs, debug_info = self.aligner.align_paragraph_runs(
                        src_text=src_text,
                        tgt_text=tgt_text,
                        runs=src_runs
                    )

                    # Add aligned runs to paragraph data
                    paragraph["aligned_runs"] = aligned_runs

                    # Add alignment metadata for debugging
                    paragraph["alignment_metadata"] = {
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
        print("Usage: python apply_alignment.py <translated.jsonl> <aligned.jsonl>")
        sys.exit(1)

    applicator = AlignmentApplicator()
    count = applicator.apply_alignment(sys.argv[1], sys.argv[2])
    print(f"Aligned {count} paragraphs")


if __name__ == "__main__":
    main()
