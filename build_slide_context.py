"""
Build slide-level context summaries from translated paragraphs.

This extracts context from translated paragraphs to help translate
charts and tables with consistent terminology.

Input: aligned_paragraphs.jsonl (after BERT alignment)
Output: slide_context.jsonl (one entry per slide with context)
"""

import json
import logging
from pathlib import Path
from collections import defaultdict
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SlideContextBuilder:
    """Build slide-level context from translated paragraphs."""

    def __init__(self):
        """Initialize context builder."""
        pass

    def build_context(
        self,
        aligned_paragraphs_jsonl: str,
        output_jsonl: str,
        max_context_chars: int = 500
    ) -> int:
        """
        Build slide context from aligned paragraphs.

        Args:
            aligned_paragraphs_jsonl: Path to aligned paragraphs JSONL
            output_jsonl: Path to output slide context JSONL
            max_context_chars: Maximum characters per slide context (default: 500)

        Returns:
            Number of slides with context

        Output format (one slide per line):
        {
            "slide_index": 0,
            "source_text": "Combined original text from all paragraphs...",
            "translated_text": "Combined translated text from all paragraphs...",
            "source_summary": "Truncated source text for context...",
            "translated_summary": "Truncated translated text for context...",
            "paragraph_count": 5
        }
        """
        logger.info(f"Building slide context from {aligned_paragraphs_jsonl}")

        # Load aligned paragraphs
        paragraphs = self._load_paragraphs(aligned_paragraphs_jsonl)

        # Group by slide
        slides_data = defaultdict(list)
        for para in paragraphs:
            slide_idx = para["slide_index"]
            slides_data[slide_idx].append(para)

        # Build context for each slide
        slide_contexts = []
        for slide_idx in sorted(slides_data.keys()):
            context = self._build_slide_context(
                slide_idx,
                slides_data[slide_idx],
                max_context_chars
            )
            slide_contexts.append(context)

        # Write output
        Path(output_jsonl).parent.mkdir(parents=True, exist_ok=True)
        with open(output_jsonl, 'w', encoding='utf-8') as f:
            for context in slide_contexts:
                f.write(json.dumps(context, ensure_ascii=False) + '\n')

        logger.info(f"Built context for {len(slide_contexts)} slides, saved to {output_jsonl}")
        return len(slide_contexts)

    def _load_paragraphs(self, jsonl_path: str) -> List[Dict]:
        """Load paragraphs from JSONL file."""
        paragraphs = []
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        para = json.loads(line)
                        # Only process paragraph content (has aligned_runs field)
                        # Skip if it's a table or chart (those have different structure)
                        if para.get("aligned_runs"):
                            paragraphs.append(para)
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decoding JSON: {e}")
                        continue
        return paragraphs

    def _build_slide_context(
        self,
        slide_idx: int,
        paragraphs: List[Dict],
        max_chars: int
    ) -> Dict:
        """
        Build context for a single slide.

        Args:
            slide_idx: Slide index
            paragraphs: List of paragraph data for this slide
            max_chars: Maximum characters for summary

        Returns:
            Slide context dict
        """
        # Extract original text from runs
        source_texts = []
        for para in paragraphs:
            # Get original text from runs or text field
            if para.get("runs"):
                text = "".join(run["text"] for run in para["runs"])
                source_texts.append(text)
            elif para.get("text"):
                source_texts.append(para["text"])

        # Extract translated text from aligned_runs
        translated_texts = []
        for para in paragraphs:
            if para.get("aligned_runs"):
                text = "".join(run["text"] for run in para["aligned_runs"])
                translated_texts.append(text)

        # Combine all text
        source_full = " ".join(source_texts)
        translated_full = " ".join(translated_texts)

        # Create summaries (truncate if too long)
        source_summary = self._truncate_text(source_full, max_chars)
        translated_summary = self._truncate_text(translated_full, max_chars)

        context = {
            "slide_index": slide_idx,
            "source_text": source_full,
            "translated_text": translated_full,
            "source_summary": source_summary,
            "translated_summary": translated_summary,
            "paragraph_count": len(paragraphs)
        }

        logger.info(f"Slide {slide_idx}: {len(paragraphs)} paragraphs, "
                   f"{len(source_full)} source chars, {len(translated_full)} translated chars")

        return context

    def _truncate_text(self, text: str, max_chars: int) -> str:
        """
        Truncate text to max characters, breaking at sentence boundary.

        Args:
            text: Text to truncate
            max_chars: Maximum characters

        Returns:
            Truncated text
        """
        if len(text) <= max_chars:
            return text

        # Try to break at sentence boundary (., !, ?)
        truncated = text[:max_chars]

        # Find last sentence boundary
        for delimiter in ['. ', '! ', '? ']:
            last_idx = truncated.rfind(delimiter)
            if last_idx > max_chars * 0.7:  # At least 70% of max_chars
                return text[:last_idx + 1]

        # No good sentence boundary, just truncate with ellipsis
        return truncated.rstrip() + "..."


def main():
    """Example usage."""
    import sys

    if len(sys.argv) < 3:
        print("Usage: python build_slide_context.py <aligned_paragraphs.jsonl> <output_context.jsonl>")
        print("\nExample:")
        print("  python build_slide_context.py temp/aligned_paragraphs.jsonl temp/slide_context.jsonl")
        sys.exit(1)

    builder = SlideContextBuilder()
    count = builder.build_context(sys.argv[1], sys.argv[2])
    print(f"\n✅ Built context for {count} slides")


if __name__ == "__main__":
    main()
