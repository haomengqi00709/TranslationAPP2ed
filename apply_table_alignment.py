"""
Apply BERT alignment to table cells to preserve formatting within cells

This module applies the same BERT alignment logic used for paragraphs
to each cell in translated tables, ensuring formatting is redistributed
correctly in the translated text.
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


class TableAlignmentApplicator:
    """Apply BERT alignment to translated table cells."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        max_phrase_length: Optional[int] = None,
        similarity_threshold: Optional[str] = None,
        glossary: Optional['TerminologyGlossary'] = None
    ):
        """
        Initialize table alignment applicator.

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

        logger.info("Initializing BERT aligner for tables")
        self.aligner = PowerPointBERTAligner(
            model_name=model_name,
            device=device,
            max_phrase_length=max_phrase_length,
            similarity_threshold=similarity_threshold,
            glossary=glossary
        )

    def apply_table_alignment(
        self,
        translated_tables_jsonl: str,
        output_jsonl: str,
        debug_jsonl: Optional[str] = None
    ) -> int:
        """
        Apply BERT alignment to table cells.

        Args:
            translated_tables_jsonl: Path to translated tables JSONL
            output_jsonl: Path to output JSONL with aligned table cells
            debug_jsonl: Optional path to write detailed alignment debug info

        Returns:
            Number of tables processed
        """
        logger.info(f"Applying BERT alignment to tables from {translated_tables_jsonl}")

        processed_count = 0
        Path(output_jsonl).parent.mkdir(parents=True, exist_ok=True)

        # Determine debug file path
        if debug_jsonl is None:
            output_path = Path(output_jsonl)
            debug_jsonl = str(output_path.parent / f"{output_path.stem}_debug{output_path.suffix}")

        Path(debug_jsonl).parent.mkdir(parents=True, exist_ok=True)

        with open(translated_tables_jsonl, 'r', encoding='utf-8') as f_in, \
             open(output_jsonl, 'w', encoding='utf-8') as f_out, \
             open(debug_jsonl, 'w', encoding='utf-8') as f_debug:

            for line_num, line in enumerate(f_in, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    table = json.loads(line)

                    logger.info(f"Aligning table {line_num} "
                              f"(slide {table.get('slide_index')}, "
                              f"{table.get('rows')}x{table.get('cols')})")

                    # Process each cell in the table
                    cells_aligned = 0
                    cells_skipped = 0
                    debug_entries = []

                    for cell in table.get("cells", []):
                        for para_idx, paragraph in enumerate(cell.get("paragraphs", [])):
                            # Check if we have original runs and translated text preserved
                            original_runs = paragraph.get("original_runs")
                            src_text = paragraph.get("original_text")
                            tgt_text = paragraph.get("translated_text")

                            # Skip if no original formatting or no translation
                            if not original_runs or not src_text or not tgt_text:
                                cells_skipped += 1
                                continue

                            if not src_text.strip() or not tgt_text.strip():
                                cells_skipped += 1
                                continue

                            try:
                                # Apply BERT alignment to this cell paragraph
                                logger.debug(f"Aligning cell ({cell['row']}, {cell['col']}) "
                                           f"para {para_idx}: {src_text[:30]}...")

                                aligned_runs, debug_info = self.aligner.align_paragraph_runs(
                                    src_text=src_text,
                                    tgt_text=tgt_text,
                                    runs=original_runs
                                )

                                # Replace the paragraph runs with aligned runs
                                paragraph["runs"] = aligned_runs
                                cells_aligned += 1

                                # Add alignment metadata
                                paragraph["alignment_metadata"] = {
                                    "source_runs_count": len(original_runs),
                                    "aligned_runs_count": len(aligned_runs),
                                    "source_text": src_text,
                                    "target_text": tgt_text
                                }

                                # Collect debug info
                                if debug_info:
                                    debug_entries.append({
                                        "cell_position": (cell['row'], cell['col']),
                                        "paragraph_index": para_idx,
                                        "source_text": src_text,
                                        "target_text": tgt_text,
                                        "source_runs_count": len(original_runs),
                                        "aligned_runs_count": len(aligned_runs),
                                        "alignment_debug": debug_info
                                    })

                                logger.debug(f"Created {len(aligned_runs)} aligned runs "
                                           f"from {len(original_runs)} source runs")

                            except Exception as e:
                                logger.error(f"Error aligning cell ({cell['row']}, {cell['col']}): {e}")
                                cells_skipped += 1
                                # Keep original runs on error
                                continue

                    # Write aligned table to output
                    f_out.write(json.dumps(table, ensure_ascii=False) + '\n')
                    processed_count += 1

                    logger.info(f"✓ Aligned {cells_aligned} cells, skipped {cells_skipped} cells in table {line_num}")

                    # Write debug info
                    if debug_entries:
                        debug_table = {
                            "slide_index": table.get("slide_index"),
                            "shape_index": table.get("shape_index"),
                            "table_size": f"{table.get('rows')}x{table.get('cols')}",
                            "cells_aligned": cells_aligned,
                            "cells_skipped": cells_skipped,
                            "cell_details": debug_entries
                        }
                        f_debug.write(json.dumps(debug_table, ensure_ascii=False) + '\n')

                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON at line {line_num}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing table at line {line_num}: {e}")
                    import traceback
                    traceback.print_exc()
                    # Write table without alignment on error
                    try:
                        f_out.write(json.dumps(table, ensure_ascii=False) + '\n')
                    except:
                        pass
                    continue

        logger.info(f"Processed {processed_count} tables to {output_jsonl}")
        logger.info(f"Debug alignment details written to {debug_jsonl}")
        return processed_count


def main():
    """Example usage."""
    import sys

    if len(sys.argv) < 3:
        print("Usage: python apply_table_alignment.py <translated_tables.jsonl> <aligned_tables.jsonl>")
        print("\nExample:")
        print("  python apply_table_alignment.py temp/translated_tables.jsonl temp/aligned_tables.jsonl")
        sys.exit(1)

    applicator = TableAlignmentApplicator()
    count = applicator.apply_table_alignment(sys.argv[1], sys.argv[2])
    print(f"\n✅ Aligned {count} tables")


if __name__ == "__main__":
    main()
