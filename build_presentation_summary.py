"""
Generate presentation summary from first 3 slides
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def generate_presentation_summary(
    extracted_text_jsonl: str,
    extracted_tables_jsonl: str,
    extracted_charts_jsonl: str,
    translator,
    max_slides: int = 3
) -> str:
    """
    Generate a 2-sentence summary describing the presentation's theme and domain.

    Uses content from the first N slides (default: 3) to understand context.

    Args:
        extracted_text_jsonl: Path to extracted text paragraphs JSONL
        extracted_tables_jsonl: Path to extracted tables JSONL
        extracted_charts_jsonl: Path to extracted charts JSONL
        translator: Translator instance to use for summary generation
        max_slides: Number of initial slides to analyze (default: 3)

    Returns:
        2-sentence summary string, or empty string if generation fails
    """
    logger.info(f"Generating presentation summary from first {max_slides} slides")

    try:
        # Collect content from first N slides
        content_parts = []

        # 1. Extract text paragraphs from first N slides
        if Path(extracted_text_jsonl).exists():
            with open(extracted_text_jsonl, 'r', encoding='utf-8') as f:
                text_count = 0
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        para = json.loads(line)
                        slide_idx = para.get('slide_index', 0)

                        if slide_idx < max_slides:
                            text = para.get('text', '').strip()
                            if text:
                                content_parts.append(f"[Slide {slide_idx}] {text}")
                                text_count += 1
                    except json.JSONDecodeError:
                        continue

                logger.info(f"Collected {text_count} text paragraphs from first {max_slides} slides")

        # 2. Extract table content from first N slides
        if Path(extracted_tables_jsonl).exists():
            with open(extracted_tables_jsonl, 'r', encoding='utf-8') as f:
                table_count = 0
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        table = json.loads(line)
                        slide_idx = table.get('slide_index', 0)

                        if slide_idx < max_slides:
                            # Extract table headers for context
                            rows = table.get('rows', [])
                            if rows:
                                # First row is usually headers
                                headers = rows[0]
                                content_parts.append(f"[Slide {slide_idx} Table] Columns: {', '.join(headers)}")
                                table_count += 1
                    except json.JSONDecodeError:
                        continue

                if table_count > 0:
                    logger.info(f"Collected {table_count} tables from first {max_slides} slides")

        # 3. Extract chart titles from first N slides
        if Path(extracted_charts_jsonl).exists():
            with open(extracted_charts_jsonl, 'r', encoding='utf-8') as f:
                chart_count = 0
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        chart = json.loads(line)
                        slide_idx = chart.get('slide_index', 0)

                        if slide_idx < max_slides:
                            title = chart.get('title', '').strip()
                            if title:
                                content_parts.append(f"[Slide {slide_idx} Chart] {title}")
                                chart_count += 1
                    except json.JSONDecodeError:
                        continue

                if chart_count > 0:
                    logger.info(f"Collected {chart_count} charts from first {max_slides} slides")

        # Check if we have any content
        if not content_parts:
            logger.warning("No content found in first slides, skipping summary generation")
            return ""

        # Limit total content to avoid token overflow (~1500 tokens max = ~6000 chars)
        combined_content = "\n".join(content_parts)
        if len(combined_content) > 6000:
            combined_content = combined_content[:6000] + "..."
            logger.info("Truncated content to 6000 characters")

        # Build prompt for summary generation
        prompt = (
            "Analyze the following content from a PowerPoint presentation and provide a concise "
            "2-sentence summary describing the main theme, topic, and domain.\n\n"
            "Focus on: subject area, target audience, and purpose.\n\n"
            f"Content:\n{combined_content}\n\n"
            "Provide ONLY a 2-sentence summary, nothing else:"
        )

        # Generate summary using translator
        logger.info("Generating summary with LLM...")
        summary = translator.translate(prompt, context=None)

        # Clean up summary (remove extra whitespace, newlines)
        summary = ' '.join(summary.split())

        # Validate: should be roughly 2 sentences (1-4 sentences acceptable)
        sentence_count = summary.count('.') + summary.count('!') + summary.count('?')
        if sentence_count < 1 or sentence_count > 4:
            logger.warning(f"Generated summary has {sentence_count} sentences (expected 2), using anyway")

        # Truncate if too long (max 300 chars)
        if len(summary) > 300:
            # Find last sentence within 300 chars
            summary_truncated = summary[:300]
            last_period = max(
                summary_truncated.rfind('.'),
                summary_truncated.rfind('!'),
                summary_truncated.rfind('?')
            )
            if last_period > 100:  # Only truncate if we have at least 100 chars
                summary = summary[:last_period + 1]
            else:
                summary = summary[:300] + "..."
            logger.info("Truncated summary to 300 characters")

        logger.info(f"Generated summary: {summary}")
        return summary

    except Exception as e:
        logger.error(f"Failed to generate presentation summary: {e}", exc_info=True)
        return ""  # Return empty string on failure (don't block pipeline)


def main():
    """Example usage for testing."""
    import sys
    from translators import LocalLLMTranslator
    import config

    if len(sys.argv) < 4:
        print("Usage: python build_presentation_summary.py <text.jsonl> <tables.jsonl> <charts.jsonl>")
        sys.exit(1)

    # Initialize translator
    translator = LocalLLMTranslator(
        model_name=config.LOCAL_MODEL_NAME,
        source_lang=config.SOURCE_LANGUAGE,
        target_lang=config.TARGET_LANGUAGE,
        device=config.LOCAL_DEVICE
    )

    # Generate summary
    summary = generate_presentation_summary(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
        translator
    )

    print("\n" + "=" * 60)
    print("PRESENTATION SUMMARY")
    print("=" * 60)
    print(summary)
    print("=" * 60)


if __name__ == "__main__":
    main()
