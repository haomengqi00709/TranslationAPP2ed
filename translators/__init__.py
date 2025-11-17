"""
Translator module for PowerPoint Translation Pipeline
Supports multiple translation backends: Local LLMs, OpenAI, Anthropic
"""

from .base import BaseTranslator
from .local_llm import LocalLLMTranslator
from .openai_translator import OpenAITranslator
from .anthropic_translator import AnthropicTranslator

__all__ = [
    "BaseTranslator",
    "LocalLLMTranslator",
    "OpenAITranslator",
    "AnthropicTranslator",
]
