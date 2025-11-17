"""
Context-aware translation for charts and tables.

This module translates charts and tables using slide context
to ensure terminology consistency with paragraph translations.
"""

import json
import logging
from typing import Optional, Dict, TYPE_CHECKING
from pathlib import Path
import config
from translators import LocalLLMTranslator, OpenAITranslator, AnthropicTranslator

if TYPE_CHECKING:
    from glossary import TerminologyGlossary

logger = logging.getLogger(__name__)


class ContentTranslator:
    """Translate charts and tables with slide context awareness."""

    def __init__(
        self,
        translator_type: Optional[str] = None,
        glossary: Optional['TerminologyGlossary'] = None
    ):
        """
        Initialize content translator.

        Args:
            translator_type: Type of translator ("local", "openai", "anthropic")
                           If None, uses config.TRANSLATOR_TYPE
            glossary: Optional terminology glossary for consistent translations
        """
        translator_type = translator_type or config.TRANSLATOR_TYPE
        self.glossary = glossary

        logger.info(f"Initializing {translator_type} content translator")

        if translator_type == "local":
            self.translator = LocalLLMTranslator(
                model_name=config.LOCAL_MODEL_NAME,
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

        logger.info(f"Content translator initialized: {self.translator}")

    def translate_charts(
        self,
        charts_jsonl: str,
        slide_context_jsonl: str,
        output_jsonl: str
    ) -> int:
        """
        Translate chart elements using slide context.

        Args:
            charts_jsonl: Path to extracted charts JSONL
            slide_context_jsonl: Path to slide context JSONL
            output_jsonl: Path to output translated charts JSONL

        Returns:
            Number of charts translated
        """
        logger.info(f"Translating charts from {charts_jsonl}")

        # Load slide contexts
        slide_contexts = self._load_slide_contexts(slide_context_jsonl)

        translated_count = 0
        Path(output_jsonl).parent.mkdir(parents=True, exist_ok=True)

        with open(charts_jsonl, 'r', encoding='utf-8') as f_in, \
             open(output_jsonl, 'w', encoding='utf-8') as f_out:

            for line_num, line in enumerate(f_in, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    chart = json.loads(line)
                    slide_idx = chart["slide_index"]

                    # Get slide context
                    context = slide_contexts.get(slide_idx, {})

                    # Translate chart elements
                    self._translate_chart(chart, context)

                    # Write to output
                    f_out.write(json.dumps(chart, ensure_ascii=False) + '\n')
                    translated_count += 1

                    logger.info(f"✓ Translated chart {line_num} on slide {slide_idx}")

                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON at line {line_num}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error translating chart at line {line_num}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue

        logger.info(f"Translated {translated_count} charts to {output_jsonl}")
        return translated_count

    def translate_tables(
        self,
        tables_jsonl: str,
        slide_context_jsonl: str,
        output_jsonl: str
    ) -> int:
        """
        Translate table cells using slide context.

        Args:
            tables_jsonl: Path to extracted tables JSONL
            slide_context_jsonl: Path to slide context JSONL
            output_jsonl: Path to output translated tables JSONL

        Returns:
            Number of tables translated
        """
        logger.info(f"Translating tables from {tables_jsonl}")

        # Load slide contexts
        slide_contexts = self._load_slide_contexts(slide_context_jsonl)

        translated_count = 0
        Path(output_jsonl).parent.mkdir(parents=True, exist_ok=True)

        with open(tables_jsonl, 'r', encoding='utf-8') as f_in, \
             open(output_jsonl, 'w', encoding='utf-8') as f_out:

            for line_num, line in enumerate(f_in, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    table = json.loads(line)
                    slide_idx = table["slide_index"]

                    # Get slide context
                    context = slide_contexts.get(slide_idx, {})

                    # Translate table cells
                    self._translate_table(table, context)

                    # Write to output
                    f_out.write(json.dumps(table, ensure_ascii=False) + '\n')
                    translated_count += 1

                    logger.info(f"✓ Translated table {line_num} on slide {slide_idx}")

                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON at line {line_num}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error translating table at line {line_num}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue

        logger.info(f"Translated {translated_count} tables to {output_jsonl}")
        return translated_count

    def _load_slide_contexts(self, context_jsonl: str) -> Dict[int, Dict]:
        """Load slide contexts indexed by slide_index."""
        contexts = {}
        with open(context_jsonl, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        context = json.loads(line)
                        slide_idx = context["slide_index"]
                        contexts[slide_idx] = context
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decoding context JSON: {e}")
                        continue
        logger.info(f"Loaded context for {len(contexts)} slides")
        return contexts

    def _translate_chart(self, chart: Dict, slide_context: Dict):
        """
        Translate all text elements in a chart.

        Args:
            chart: Chart data dict (modified in-place)
            slide_context: Slide context dict with source/translated text
        """
        # Build context prompt for charts
        context_prompt = self._build_chart_context(slide_context)

        # Add glossary context if available
        if self.glossary:
            # Get all text from chart for glossary matching
            chart_texts = []
            if chart.get("title") and chart["title"].get("text"):
                chart_texts.append(chart["title"]["text"])
            if chart.get("axis_titles"):
                for axis_type in ["category", "value"]:
                    if chart["axis_titles"].get(axis_type) and chart["axis_titles"][axis_type].get("text"):
                        chart_texts.append(chart["axis_titles"][axis_type]["text"])

            combined_text = " ".join(chart_texts)
            glossary_context = self.glossary.get_prompt_context(combined_text)
            if glossary_context:
                context_prompt = glossary_context + "\n\n" + context_prompt if context_prompt else glossary_context

        # Translate chart title
        if chart.get("title") and chart["title"].get("text"):
            original_title = chart["title"]["text"]
            logger.info(f"  Translating title: {original_title}")
            translated_title = self.translator.translate(original_title, context=context_prompt)
            chart["title"]["text"] = translated_title
            logger.info(f"  → {translated_title}")

        # Translate axis titles
        if chart.get("axis_titles"):
            for axis_type in ["category", "value"]:
                if chart["axis_titles"].get(axis_type) and chart["axis_titles"][axis_type].get("text"):
                    original_text = chart["axis_titles"][axis_type]["text"]
                    logger.info(f"  Translating {axis_type} axis: {original_text}")
                    translated_text = self.translator.translate(original_text, context=context_prompt)
                    chart["axis_titles"][axis_type]["text"] = translated_text
                    logger.info(f"  → {translated_text}")

        # Translate legend entries
        if chart.get("legend_entries"):
            for entry in chart["legend_entries"]:
                original_text = entry["text"]
                logger.info(f"  Translating legend: {original_text}")
                translated_text = self.translator.translate(original_text, context=context_prompt)
                entry["text"] = translated_text
                logger.info(f"  → {translated_text}")

        # Translate category labels
        if chart.get("category_labels"):
            for label in chart["category_labels"]:
                original_text = label["text"]
                logger.info(f"  Translating category: {original_text}")
                translated_text = self.translator.translate(original_text, context=context_prompt)
                label["text"] = translated_text
                logger.info(f"  → {translated_text}")

    def _translate_table(self, table: Dict, slide_context: Dict):
        """
        Translate all text in table cells.

        Args:
            table: Table data dict (modified in-place)
            slide_context: Slide context dict with source/translated text
        """
        # Build context prompt for tables
        context_prompt = self._build_table_context(slide_context)

        # Add glossary context if available
        if self.glossary:
            # Get sample text from table for glossary matching
            table_texts = []
            if table.get("cells"):
                for cell in table["cells"][:20]:  # Sample first 20 cells
                    for paragraph in cell.get("paragraphs", []):
                        text = "".join(run["text"] for run in paragraph.get("runs", []))
                        if text.strip():
                            table_texts.append(text)

            if table_texts:
                combined_text = " ".join(table_texts)
                glossary_context = self.glossary.get_prompt_context(combined_text)
                if glossary_context:
                    context_prompt = glossary_context + "\n\n" + context_prompt if context_prompt else glossary_context

        # Translate each cell
        if table.get("cells"):
            for cell in table["cells"]:
                for paragraph in cell.get("paragraphs", []):
                    # Combine run text
                    original_text = "".join(run["text"] for run in paragraph.get("runs", []))

                    if not original_text.strip():
                        continue

                    logger.debug(f"  Translating cell ({cell['row']}, {cell['col']}): {original_text}")
                    translated_text = self.translator.translate(original_text, context=context_prompt)

                    # Store translated text and preserve original runs for BERT alignment
                    if paragraph.get("runs"):
                        # Preserve original runs for later BERT alignment
                        paragraph["original_runs"] = paragraph["runs"].copy()
                        paragraph["original_text"] = original_text
                        paragraph["translated_text"] = translated_text

                        # Keep formatting from first run (temporary single-run version)
                        first_run = paragraph["runs"][0]
                        paragraph["runs"] = [{
                            "run_index": 0,
                            "text": translated_text,
                            "font": first_run.get("font"),
                            "size": first_run.get("size"),
                            "bold": first_run.get("bold"),
                            "italic": first_run.get("italic"),
                            "underline": first_run.get("underline"),
                            "color": first_run.get("color"),
                            "hyperlink": first_run.get("hyperlink"),
                            "superscript": first_run.get("superscript"),
                            "subscript": first_run.get("subscript")
                        }]

                    logger.debug(f"  → {translated_text}")

    def _build_chart_context(self, slide_context: Dict) -> str:
        """
        Build context prompt for chart translation.

        Args:
            slide_context: Slide context dict

        Returns:
            Context string for translation prompt
        """
        if not slide_context:
            return ""

        source_summary = slide_context.get("source_summary", "")
        translated_summary = slide_context.get("translated_summary", "")

        context = f"""
SLIDE CONTEXT (for terminology consistency):

Original slide content:
{source_summary}

Translated slide content:
{translated_summary}

INSTRUCTIONS:
- Translate chart labels using the SAME terminology as shown in the slide context above
- Keep translations concise and appropriate for chart labels
- Match the style and vocabulary used in the translated slide content
""".strip()

        return context

    def _build_table_context(self, slide_context: Dict) -> str:
        """
        Build context prompt for table translation.

        Args:
            slide_context: Slide context dict

        Returns:
            Context string for translation prompt
        """
        if not slide_context:
            return ""

        source_summary = slide_context.get("source_summary", "")
        translated_summary = slide_context.get("translated_summary", "")

        context = f"""
SLIDE CONTEXT (for terminology consistency):

Original slide content:
{source_summary}

Translated slide content:
{translated_summary}

INSTRUCTIONS:
- Translate table cells using the SAME terminology as shown in the slide context above
- Preserve the intent (headers, data, labels)
- Match the style and vocabulary used in the translated slide content
""".strip()

        return context


def main():
    """Example usage."""
    import sys

    if len(sys.argv) < 5:
        print("Usage: python translate_content.py <content_type> <input.jsonl> <slide_context.jsonl> <output.jsonl> [translator_type]")
        print("\nExamples:")
        print("  python translate_content.py charts temp/extracted_charts.jsonl temp/slide_context.jsonl temp/translated_charts.jsonl")
        print("  python translate_content.py tables temp/extracted_tables.jsonl temp/slide_context.jsonl temp/translated_tables.jsonl")
        sys.exit(1)

    content_type = sys.argv[1]
    input_jsonl = sys.argv[2]
    context_jsonl = sys.argv[3]
    output_jsonl = sys.argv[4]
    translator_type = sys.argv[5] if len(sys.argv) > 5 else None

    translator = ContentTranslator(translator_type=translator_type)

    if content_type == "charts":
        count = translator.translate_charts(input_jsonl, context_jsonl, output_jsonl)
        print(f"\n✅ Translated {count} charts")
    elif content_type == "tables":
        count = translator.translate_tables(input_jsonl, context_jsonl, output_jsonl)
        print(f"\n✅ Translated {count} tables")
    else:
        print(f"Unknown content type: {content_type}")
        sys.exit(1)


if __name__ == "__main__":
    main()
