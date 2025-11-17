"""
Anthropic API translator (Claude)
"""

import logging
from typing import Optional

from .base import BaseTranslator

logger = logging.getLogger(__name__)


class AnthropicTranslator(BaseTranslator):
    """Translator using Anthropic Claude API."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        source_lang: str = "English",
        target_lang: str = "French",
        temperature: float = 0.3,
        max_tokens: int = 500,
    ):
        """
        Initialize Anthropic translator.

        Args:
            api_key: Anthropic API key
            model: Model name (e.g., claude-3-opus, claude-3-sonnet, claude-3-haiku)
            source_lang: Source language name
            target_lang: Target language name
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        super().__init__(source_lang, target_lang)

        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError(
                "Anthropic package not installed. Install with: pip install anthropic"
            )

        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        logger.info(f"Initialized Anthropic translator with model {model}")

    def translate(self, text: str, context: Optional[str] = None) -> str:
        """
        Translate text using Anthropic API.

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
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_content,
                messages=[
                    {"role": "user", "content": text}
                ]
            )

            translation = response.content[0].text.strip()
            return translation

        except Exception as e:
            logger.error(f"Anthropic translation error: {str(e)}")
            return text  # Return original text if translation fails
