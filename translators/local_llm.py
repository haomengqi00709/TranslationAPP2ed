"""
Local LLM translator using Hugging Face transformers
"""

import torch
import logging
from typing import Optional
from transformers import AutoModelForCausalLM, AutoTokenizer

from .base import BaseTranslator

logger = logging.getLogger(__name__)


class LocalLLMTranslator(BaseTranslator):
    """Translator using local Hugging Face models."""

    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-8B",
        source_lang: str = "English",
        target_lang: str = "French",
        device: str = "auto",
        temperature: float = 0.8,
        max_tokens: int = 200,
    ):
        """
        Initialize local LLM translator.

        Args:
            model_name: Hugging Face model name
            source_lang: Source language name
            target_lang: Target language name
            device: Device to use ("auto", "cuda", "mps", "cpu")
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        super().__init__(source_lang, target_lang)

        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Device selection
        if device == "auto":
            if torch.cuda.is_available():
                self.device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                # Double-check MPS is truly available (may be disabled in runpod_handler.py)
                try:
                    # Try to create a tensor on MPS
                    _ = torch.zeros(1, device="mps")
                    self.device = "mps"
                except:
                    # MPS is disabled or unavailable
                    self.device = "cpu"
            else:
                self.device = "cpu"
        else:
            self.device = device

        logger.info(f"Loading model {model_name} on device {self.device}")

        # Load model and tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if self.device in ["cuda", "mps"] else torch.float32,
            device_map=self.device
        )
        self.model.eval()

        logger.info(f"Model loaded successfully on {self.device}")

    def translate(self, text: str, context: Optional[str] = None) -> str:
        """
        Translate text using local LLM.

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

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": text}
        ]

        try:
            # Apply chat template
            prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False
            )

            # Tokenize
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.max_tokens,
                    temperature=self.temperature,
                    top_p=0.95,
                    top_k=20,
                    do_sample=True
                )

            # Decode
            translation = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Extract only the translation (after "assistant")
            if "assistant" in translation:
                translation = translation.split("assistant")[-1].strip()

            # Clean up any thinking tags
            translation = translation.replace("<think>", "").replace("</think>", "")
            translation = translation.replace("\n\n", " ").strip()

            return translation

        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            return text  # Return original text if translation fails

