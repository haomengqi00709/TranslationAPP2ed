"""
OpenAI API translator (GPT-4, GPT-3.5, etc.)
"""

import logging
from typing import Optional

from .base import BaseTranslator

logger = logging.getLogger(__name__)


class OpenAITranslator(BaseTranslator):
    """Translator using OpenAI API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        source_lang: str = "English",
        target_lang: str = "French",
        temperature: float = 0.3,
        max_tokens: int = 500,
    ):
        """
        Initialize OpenAI translator.

        Args:
            api_key: OpenAI API key
            model: Model name (e.g., gpt-4, gpt-4o-mini, gpt-3.5-turbo)
            source_lang: Source language name
            target_lang: Target language name
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        super().__init__(source_lang, target_lang)

        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "OpenAI package not installed. Install with: pip install openai"
            )

        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        logger.info(f"Initialized OpenAI translator with model {model}")

    def translate(self, text: str, context: Optional[str] = None) -> str:
        """
        Translate text using OpenAI API.

        Args:
            text: Text to translate
            context: Optional context for better translation

        Returns:
            Translated text
        """
        if not text or not text.strip():
            return text

        # Build system prompt
        if context:
            system_content = (
                f"{context}\n\n"
                f"You are a professional translator. Translate the following {self.source_lang} text to {self.target_lang}. "
                f"Only output the {self.target_lang} translation, nothing else."
            )
        else:
            system_content = (
                f"You are a professional translator. Translate the following {self.source_lang} text to {self.target_lang}. "
                f"Only output the {self.target_lang} translation, nothing else."
            )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": text}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            translation = response.choices[0].message.content.strip()
            return translation

        except Exception as e:
            logger.error(f"OpenAI translation error: {str(e)}")
            return text  # Return original text if translation fails

    def batch_translate(self, texts: list[str], context: Optional[str] = None) -> list[str]:
        """
        Translate multiple texts. OpenAI doesn't have native batch support in chat API,
        so we translate one by one.
        """
        return [self.translate(text, context) for text in texts]
