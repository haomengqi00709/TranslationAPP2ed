"""
Paragraph-level translation using translator interface
"""

import json
import logging
from typing import Optional, TYPE_CHECKING
from pathlib import Path
import config
from translators import LocalLLMTranslator, OpenAITranslator, AnthropicTranslator

if TYPE_CHECKING:
    from glossary import TerminologyGlossary

logger = logging.getLogger(__name__)


class ParagraphTranslator:
    """Translate paragraphs using configured translator."""

    def __init__(
        self,
        translator_type: Optional[str] = None,
        glossary: Optional['TerminologyGlossary'] = None
    ):
        """
        Initialize paragraph translator.

        Args:
            translator_type: Type of translator ("local", "openai", "anthropic")
                           If None, uses config.TRANSLATOR_TYPE
            glossary: Optional terminology glossary for consistent translations
        """
        translator_type = translator_type or config.TRANSLATOR_TYPE
        self.glossary = glossary

        logger.info(f"Initializing {translator_type} translator")

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

        logger.info(f"Translator initialized: {self.translator}")

    def translate_paragraphs(
        self,
        input_jsonl: str,
        output_jsonl: str,
        context: Optional[str] = None
    ) -> int:
        """
        Translate paragraphs from input JSONL to output JSONL.

        Args:
            input_jsonl: Path to input JSONL file with extracted paragraphs
            output_jsonl: Path to output JSONL file with translations
            context: Optional context for translation (e.g., glossary terms)

        Returns:
            Number of paragraphs translated
        """
        logger.info(f"Translating paragraphs from {input_jsonl}")

        translated_count = 0
        Path(output_jsonl).parent.mkdir(parents=True, exist_ok=True)

        with open(input_jsonl, 'r', encoding='utf-8') as f_in, \
             open(output_jsonl, 'w', encoding='utf-8') as f_out:

            for line_num, line in enumerate(f_in, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    paragraph = json.loads(line)

                    # Get paragraph text
                    src_text = paragraph["text"]

                    if not src_text.strip():
                        # Empty paragraph, skip translation
                        paragraph["translated_text"] = ""
                        f_out.write(json.dumps(paragraph, ensure_ascii=False) + '\n')
                        continue

                    # Build context with glossary if available
                    full_context = context or ""
                    if self.glossary:
                        glossary_context = self.glossary.get_prompt_context(src_text)
                        if glossary_context:
                            if full_context:
                                full_context = glossary_context + "\n\n" + full_context
                            else:
                                full_context = glossary_context

                    # Translate paragraph
                    logger.info(f"Translating paragraph {line_num}: {src_text[:50]}...")
                    translated_text = self.translator.translate(src_text, context=full_context)

                    # Add translation to paragraph data
                    paragraph["translated_text"] = translated_text

                    # Write to output
                    f_out.write(json.dumps(paragraph, ensure_ascii=False) + '\n')
                    translated_count += 1

                    logger.debug(f"Translation: {translated_text[:50]}...")

                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON at line {line_num}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error translating paragraph at line {line_num}: {e}")
                    # Write original paragraph on error
                    try:
                        paragraph["translated_text"] = src_text
                        f_out.write(json.dumps(paragraph, ensure_ascii=False) + '\n')
                    except:
                        pass
                    continue

        logger.info(f"Translated {translated_count} paragraphs to {output_jsonl}")
        return translated_count


def main():
    """Example usage."""
    import sys

    if len(sys.argv) < 3:
        print("Usage: python translate_paragraphs.py <input.jsonl> <output.jsonl> [translator_type]")
        sys.exit(1)

    translator_type = sys.argv[3] if len(sys.argv) > 3 else None
    translator = ParagraphTranslator(translator_type=translator_type)
    count = translator.translate_paragraphs(sys.argv[1], sys.argv[2])
    print(f"Translated {count} paragraphs")


if __name__ == "__main__":
    main()
