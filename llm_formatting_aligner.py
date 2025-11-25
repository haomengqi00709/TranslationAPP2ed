"""
LLM-based formatting alignment for PowerPoint translation.

This aligner uses LLM to map formatted English terms to their French equivalents,
then applies the formatting to the matched French text.

This is completely independent from BERT alignment for comparison purposes.
"""

import json
import logging
import re
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class LLMFormattingAligner:
    """LLM-based aligner for applying formatting to translated text."""

    def __init__(self, translator=None):
        """
        Initialize LLM formatting aligner.

        Args:
            translator: Translator instance for LLM calls.
                       If None, will need to be set before use.
        """
        self.translator = translator

    def set_translator(self, translator):
        """Set the translator instance."""
        self.translator = translator

    def extract_formatted_runs(self, runs: List[Dict]) -> List[Dict]:
        """
        Extract runs that have special formatting (bold, italic, color, etc.).

        Enhanced to detect:
        - Traditional formatting: bold, italic, underline, color
        - Emphasis via size/font differences from paragraph baseline
        - Hyperlinks (always special)

        Args:
            runs: List of run dictionaries

        Returns:
            List of formatted runs with merged consecutive runs
        """
        if not runs:
            return []

        # First, determine baseline font and size (most common in paragraph)
        baseline_font = self._get_baseline_font(runs)
        baseline_size = self._get_baseline_size(runs)

        formatted_runs = []

        for i, run in enumerate(runs):
            # Check for traditional special formatting
            has_traditional_format = (
                run.get("bold", False) or
                run.get("italic", False) or
                run.get("underline", False) or
                run.get("superscript", False) or
                run.get("subscript", False) or
                (run.get("color") and run.get("color") != "#FFFFFF" and not run.get("color", "").startswith("theme:BACKGROUND"))
            )

            # Check for emphasis via size/font difference
            has_size_emphasis = (baseline_size and run.get("size") and run.get("size") != baseline_size)
            has_font_emphasis = (baseline_font and run.get("font") and run.get("font") != baseline_font)

            # Check for hyperlink
            has_hyperlink = bool(run.get("hyperlink"))

            # Run is special if it has ANY of these
            is_special = (
                has_traditional_format or
                has_size_emphasis or
                has_font_emphasis or
                has_hyperlink
            )

            if is_special:
                # Skip whitespace-only runs to prevent color bleeding
                # (e.g., a space character with yellow color shouldn't be treated as special)
                if run.get("text", "").strip():  # Only add if has non-whitespace content
                    # Add the original index to track true consecutiveness
                    run_copy = run.copy()
                    run_copy["_original_index"] = i
                    formatted_runs.append(run_copy)

        # Merge ONLY truly consecutive runs with identical formatting
        merged_runs = self._merge_consecutive_formatted_runs(formatted_runs)

        logger.debug(f"Extracted {len(merged_runs)} formatted run blocks from {len(runs)} total runs (baseline: font={baseline_font}, size={baseline_size})")
        return merged_runs

    def _get_baseline_font(self, runs: List[Dict]) -> Optional[str]:
        """Get the most common font in the paragraph."""
        from collections import Counter
        fonts = [run.get("font") for run in runs if run.get("font")]
        if fonts:
            return Counter(fonts).most_common(1)[0][0]
        return None

    def _get_baseline_size(self, runs: List[Dict]) -> Optional[float]:
        """Get the most common font size in the paragraph."""
        from collections import Counter
        sizes = [run.get("size") for run in runs if run.get("size")]
        if sizes:
            return Counter(sizes).most_common(1)[0][0]
        return None

    def _merge_consecutive_formatted_runs(self, runs: List[Dict]) -> List[Dict]:
        """
        Merge ONLY truly consecutive runs that have identical formatting.

        This handles cases like:
        Run 0: "Legislative" (bold+yellow)
        Run 1: " " (bold+yellow)  ← consecutive in original (index 0, 1)
        Run 2: "Branch" (bold+yellow)  ← consecutive in original (index 1, 2)
        → Merged: "Legislative Branch" (bold+yellow)

        But SKIPS cases like:
        Run 0: "federal" (bold+yellow)
        Run 2: "municipal" (bold+yellow)  ← NOT consecutive (index 0, 2 - missing 1)
        → Kept separate: ["federal"], ["municipal"]
        """
        if not runs:
            return []

        merged = []
        current_group = None
        last_index = None

        for run in runs:
            current_index = run.get("_original_index")

            if current_group is None:
                # Start new group
                current_group = {
                    "text": run.get("text", ""),
                    "bold": run.get("bold", False),
                    "italic": run.get("italic", False),
                    "underline": run.get("underline", False),
                    "font": run.get("font"),
                    "size": run.get("size"),
                    "color": run.get("color"),
                    "superscript": run.get("superscript", False),
                    "subscript": run.get("subscript", False),
                    "hyperlink": run.get("hyperlink")
                }
                last_index = current_index
            else:
                # Check if truly consecutive AND formatting matches
                is_consecutive = (current_index == last_index + 1)
                formatting_matches = (
                    current_group["bold"] == run.get("bold", False) and
                    current_group["italic"] == run.get("italic", False) and
                    current_group["underline"] == run.get("underline", False) and
                    current_group["font"] == run.get("font") and
                    current_group["size"] == run.get("size") and
                    current_group["color"] == run.get("color") and
                    current_group["superscript"] == run.get("superscript", False) and
                    current_group["subscript"] == run.get("subscript", False) and
                    current_group["hyperlink"] == run.get("hyperlink")
                )

                if is_consecutive and formatting_matches:
                    # Truly consecutive with same formatting - merge text
                    current_group["text"] += run.get("text", "")
                    last_index = current_index
                else:
                    # Not consecutive OR different formatting - save current group and start new one
                    if current_group["text"].strip():
                        merged.append(current_group)
                    current_group = {
                        "text": run.get("text", ""),
                        "bold": run.get("bold", False),
                        "italic": run.get("italic", False),
                        "underline": run.get("underline", False),
                        "font": run.get("font"),
                        "size": run.get("size"),
                        "color": run.get("color"),
                        "superscript": run.get("superscript", False),
                        "subscript": run.get("subscript", False),
                        "hyperlink": run.get("hyperlink")
                    }
                    last_index = current_index

        # Add final group
        if current_group and current_group["text"].strip():
            merged.append(current_group)

        return merged

    def ask_llm_for_mapping_individual(
        self,
        source_term: str,
        source_text: str,
        target_text: str,
        source_lang: str = "English",
        target_lang: str = "French"
    ) -> Optional[str]:
        """
        Ask LLM to map a SINGLE formatted term to its translation.

        Args:
            source_term: Single source term to map
            source_text: Full source paragraph
            target_text: Full translated paragraph
            source_lang: Source language name
            target_lang: Target language name

        Returns:
            Target term or None
        """
        if not self.translator:
            raise ValueError("Translator not set. Call set_translator() first.")

        if not source_term.strip():
            return None

        prompt = f"""Given this translation:

{source_lang}: "{source_text}"
{target_lang}: "{target_text}"

Find where "{source_term}" appears in the {target_lang} translation above.

IMPORTANT:
- Return the EXACT {target_lang} text that corresponds to "{source_term}"
- Copy it EXACTLY as it appears in the {target_lang} sentence (with correct capitalization, accents, articles)
- Do NOT translate it yourself - just find and return what's already in the {target_lang} text
- Return ONLY the {target_lang} phrase (no explanation, no quotes, no extra words)

{target_lang} equivalent:"""

        try:
            result = self.translator.translate(prompt, context=None)

            # Clean up response
            target_term = result.strip().strip('"').strip()

            if target_term:
                logger.debug(f"LLM mapped '{source_term}' → '{target_term}'")
                return target_term
            else:
                logger.warning(f"Empty response for '{source_term}'")
                return None

        except Exception as e:
            logger.error(f"LLM mapping failed for '{source_term}': {e}")
            return None

    def find_text_in_paragraph(
        self,
        search_text: str,
        target_text: str,
        used_positions: set = None
    ) -> Optional[Tuple[int, int, str]]:
        """
        Find text in paragraph with fuzzy matching fallback.

        Args:
            search_text: Text to find
            target_text: Text to search in
            used_positions: Set of character positions already used

        Returns:
            Tuple of (start, end, matched_text) or None
        """
        if not search_text:
            return None

        if used_positions is None:
            used_positions = set()

        search_lower = search_text.lower().strip()
        target_lower = target_text.lower()

        # Strategy 1: Exact case-insensitive match
        idx = target_lower.find(search_lower)
        if idx != -1:
            end = idx + len(search_text)
            position_range = set(range(idx, end))
            if not (position_range & used_positions):
                matched = target_text[idx:end]
                return (idx, end, matched)

        # Strategy 2: Word boundary match
        try:
            pattern = re.compile(r'\b' + re.escape(search_lower) + r'\b', re.IGNORECASE)
            for match in pattern.finditer(target_text):
                position_range = set(range(match.start(), match.end()))
                if not (position_range & used_positions):
                    return (match.start(), match.end(), match.group())
        except re.error:
            pass

        # Strategy 3: Partial match (search is substring)
        start = 0
        while True:
            idx = target_lower.find(search_lower, start)
            if idx == -1:
                break

            end = idx + len(search_lower)
            position_range = set(range(idx, end))
            if not (position_range & used_positions):
                matched = target_text[idx:end]
                return (idx, end, matched)

            start = idx + 1

        logger.warning(f"Could not find '{search_text}' in target text")
        return None

    def build_aligned_runs(
        self,
        target_text: str,
        base_format: Dict,
        formatted_mappings: List[Dict]
    ) -> List[Dict]:
        """
        Build target runs with formatting applied to matched terms.

        Args:
            target_text: Full translated text
            base_format: Base formatting for non-formatted text
            formatted_mappings: List of mappings with positions and formats

        Returns:
            List of run dictionaries
        """
        if not formatted_mappings:
            # No formatting, return single run with base format
            return [{
                "text": target_text,
                **base_format
            }]

        # Sort mappings by position
        sorted_mappings = sorted(formatted_mappings, key=lambda x: x["start"])

        runs = []
        current_pos = 0

        for mapping in sorted_mappings:
            start = mapping["start"]
            end = mapping["end"]
            matched_text = mapping["matched_text"]
            format_info = mapping["format"]

            # Add text before this match with base formatting
            if start > current_pos:
                before_text = target_text[current_pos:start]
                if before_text:
                    runs.append({
                        "text": before_text,
                        **base_format
                    })

            # Add the formatted match
            runs.append({
                "text": matched_text,
                **format_info
            })

            current_pos = end

        # Add remaining text with base formatting
        if current_pos < len(target_text):
            remaining = target_text[current_pos:]
            if remaining:
                runs.append({
                    "text": remaining,
                    **base_format
                })

        # Merge consecutive runs with identical formatting
        merged_runs = self._merge_identical_runs(runs)

        return merged_runs

    def _merge_identical_runs(self, runs: List[Dict]) -> List[Dict]:
        """Merge consecutive runs that have identical formatting."""
        if not runs:
            return runs

        merged = [runs[0].copy()]

        for run in runs[1:]:
            last = merged[-1]
            # Check if formatting is identical
            if (last.get("bold") == run.get("bold") and
                last.get("italic") == run.get("italic") and
                last.get("underline") == run.get("underline") and
                last.get("font") == run.get("font") and
                last.get("size") == run.get("size") and
                last.get("color") == run.get("color") and
                last.get("superscript") == run.get("superscript") and
                last.get("subscript") == run.get("subscript") and
                last.get("hyperlink") == run.get("hyperlink")):
                # Merge text
                last["text"] += run["text"]
            else:
                # Different formatting
                merged.append(run.copy())

        return merged

    def get_base_formatting(self, runs: List[Dict]) -> Dict:
        """
        Get the base/default formatting from runs.

        Uses the longest non-formatted run as the base.
        """
        if not runs:
            return {
                "bold": False,
                "italic": False,
                "underline": False,
                "font": None,
                "size": None,
                "color": None,
                "superscript": False,
                "subscript": False,
                "hyperlink": None
            }

        # Find longest run without special formatting
        normal_runs = []
        for run in runs:
            has_special = (
                run.get("bold", False) or
                run.get("italic", False) or
                run.get("underline", False) or
                (run.get("color") and
                 run.get("color") != "#FFFFFF" and
                 not run.get("color", "").startswith("theme:BACKGROUND"))
            )
            if not has_special:
                normal_runs.append(run)

        if normal_runs:
            base_run = max(normal_runs, key=lambda x: len(x.get("text", "")))
        else:
            base_run = runs[0]

        return {
            "bold": False,
            "italic": False,
            "underline": False,
            "font": base_run.get("font"),
            "size": base_run.get("size"),
            "color": base_run.get("color"),
            "superscript": False,
            "subscript": False,
            "hyperlink": None
        }

    def align_paragraph_runs(
        self,
        src_text: str,
        tgt_text: str,
        runs: List[Dict],
        source_lang: str = "English",
        target_lang: str = "French"
    ) -> Tuple[List[Dict], Optional[Dict]]:
        """
        Main alignment function using LLM.

        Args:
            src_text: Source paragraph text
            tgt_text: Target paragraph text
            runs: Source runs with formatting
            source_lang: Source language name
            target_lang: Target language name

        Returns:
            Tuple of (target_runs, debug_info)
        """
        if not src_text.strip() or not tgt_text.strip():
            logger.warning("Empty source or target text")
            return [{
                "text": tgt_text,
                "bold": False,
                "italic": False,
                "underline": False,
                "font": None,
                "size": None,
                "color": None,
                "superscript": False,
                "subscript": False,
                "hyperlink": None
            }], None

        # Handle single run case
        if len(runs) == 1:
            logger.debug("Single run detected, applying uniform formatting")
            return [{
                "text": tgt_text,
                "bold": runs[0].get("bold", False),
                "italic": runs[0].get("italic", False),
                "underline": runs[0].get("underline", False),
                "font": runs[0].get("font"),
                "size": runs[0].get("size"),
                "color": runs[0].get("color"),
                "superscript": runs[0].get("superscript", False),
                "subscript": runs[0].get("subscript", False),
                "hyperlink": runs[0].get("hyperlink")
            }], {"alignment_type": "single_run"}

        # Extract runs with special formatting
        formatted_runs = self.extract_formatted_runs(runs)

        if not formatted_runs:
            # No special formatting, use base format
            base_format = self.get_base_formatting(runs)
            return [{
                "text": tgt_text,
                **base_format
            }], {"alignment_type": "no_formatting"}

        # Get base formatting
        base_format = self.get_base_formatting(runs)

        # Ask LLM for mappings - ONE BY ONE for better reliability
        logger.info(f"Asking LLM to map {len(formatted_runs)} formatted terms (individually)")

        # Find each formatted run's equivalent in target text
        formatted_mappings = []
        used_positions = set()
        successful_mappings = 0

        for i, formatted_run in enumerate(formatted_runs, 1):
            source_term = formatted_run["text"].strip()

            logger.info(f"[{i}/{len(formatted_runs)}] Mapping '{source_term}'")

            # Ask LLM for this specific term
            target_term = self.ask_llm_for_mapping_individual(
                source_term,
                src_text,
                tgt_text,
                source_lang,
                target_lang
            )

            if target_term:
                # Find in target text
                position = self.find_text_in_paragraph(target_term, tgt_text, used_positions)

                if position:
                    start, end, matched_text = position
                    formatted_mappings.append({
                        "source_term": source_term,
                        "target_term": target_term,
                        "matched_text": matched_text,
                        "start": start,
                        "end": end,
                        "format": {
                            "bold": formatted_run.get("bold", False),
                            "italic": formatted_run.get("italic", False),
                            "underline": formatted_run.get("underline", False),
                            "font": formatted_run.get("font"),
                            "size": formatted_run.get("size"),
                            "color": formatted_run.get("color"),
                            "superscript": formatted_run.get("superscript", False),
                            "subscript": formatted_run.get("subscript", False),
                            "hyperlink": formatted_run.get("hyperlink")
                        }
                    })
                    # Mark positions as used
                    used_positions.update(range(start, end))
                    successful_mappings += 1
                    logger.info(f"✓ Mapped '{source_term}' → '{matched_text}' at {start}-{end}")
                else:
                    logger.warning(f"✗ Could not find '{target_term}' in target text")
            else:
                logger.warning(f"✗ LLM did not provide mapping for '{source_term}'")

        # Build final runs
        aligned_runs = self.build_aligned_runs(tgt_text, base_format, formatted_mappings)

        # Build debug info with individual mappings
        individual_mappings = {}
        for mapping in formatted_mappings:
            individual_mappings[mapping["source_term"]] = mapping["target_term"]

        debug_info = {
            "alignment_type": "llm_individual",
            "formatted_runs_count": len(formatted_runs),
            "successful_mappings": successful_mappings,
            "failed_mappings": len(formatted_runs) - successful_mappings,
            "individual_mappings": individual_mappings
        }

        logger.info(f"LLM alignment complete: {successful_mappings}/{len(formatted_runs)} terms mapped, {len(aligned_runs)} runs created")

        return aligned_runs, debug_info


def main():
    """Test the LLM formatting aligner."""
    print("LLM Formatting Aligner - use apply_alignment.py to integrate")


if __name__ == "__main__":
    main()
