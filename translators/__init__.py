"""
Translator module for PowerPoint Translation Pipeline
Supports multiple translation backends: Local LLMs, OpenAI, Anthropic
"""

from .base import BaseTranslator
from .openai_translator import OpenAITranslator
from .anthropic_translator import AnthropicTranslator

# Only import LocalLLMTranslator if torch is available (not needed on Railway)
try:
    from .local_llm import LocalLLMTranslator
    __all__ = [
        "BaseTranslator",
        "LocalLLMTranslator",
        "OpenAITranslator",
        "AnthropicTranslator",
    ]
except ImportError:
    # torch not available - skip LocalLLMTranslator (Railway deployment)
    LocalLLMTranslator = None
    __all__ = [
        "BaseTranslator",
        "OpenAITranslator",
        "AnthropicTranslator",
    ]
