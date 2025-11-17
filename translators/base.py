"""
Base translator interface
"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseTranslator(ABC):
    """Abstract base class for all translators."""

    def __init__(self, source_lang: str = "English", target_lang: str = "French"):
        """
        Initialize translator.

        Args:
            source_lang: Source language name
            target_lang: Target language name
        """
        self.source_lang = source_lang
        self.target_lang = target_lang

    @abstractmethod
    def translate(self, text: str, context: Optional[str] = None) -> str:
        """
        Translate text from source language to target language.

        Args:
            text: Text to translate
            context: Optional context for better translation (e.g., RAG context)

        Returns:
            Translated text
        """
        raise NotImplementedError("Subclasses must implement translate()")

    def batch_translate(self, texts: list[str], context: Optional[str] = None) -> list[str]:
        """
        Translate multiple texts. Default implementation translates one by one.
        Subclasses can override for more efficient batch processing.

        Args:
            texts: List of texts to translate
            context: Optional context for better translation

        Returns:
            List of translated texts
        """
        return [self.translate(text, context) for text in texts]

    def __repr__(self):
        return f"{self.__class__.__name__}({self.source_lang} -> {self.target_lang})"
