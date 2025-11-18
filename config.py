"""
Configuration file for PowerPoint Translation Pipeline with BERT Alignment
"""

import os
from pathlib import Path

# ============================================================================
# Translator Configuration
# ============================================================================

# Translator type: "openai", "anthropic", "gemini", "local"
TRANSLATOR_TYPE = "local"

# ============================================================================
# API Settings
# ============================================================================

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o-mini"  # Options: gpt-4, gpt-4o, gpt-4o-mini, gpt-3.5-turbo
OPENAI_TEMPERATURE = 0.3
OPENAI_MAX_TOKENS = 500

# Anthropic Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"  # Options: claude-3-opus, claude-3-sonnet, claude-3-haiku
ANTHROPIC_TEMPERATURE = 0.3
ANTHROPIC_MAX_TOKENS = 500

# Google Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-1.5-flash"  # Options: gemini-1.5-pro, gemini-1.5-flash
GEMINI_TEMPERATURE = 0.3
GEMINI_MAX_TOKENS = 500

# ============================================================================
# Local Model Settings
# ============================================================================

LOCAL_MODEL_NAME = "Qwen/Qwen3-8B"
LOCAL_MODEL_14B_NAME = "Qwen/Qwen3-14B"  # Better model, larger and more accurate
LOCAL_DEVICE = "mps"  # "auto", "cuda", "mps", "cpu"
LOCAL_TEMPERATURE = 0.8
LOCAL_MAX_TOKENS = 200

# ============================================================================
# BERT Alignment Settings
# ============================================================================

BERT_MODEL_NAME = "sentence-transformers/LaBSE"
BERT_DEVICE = "cpu"  # "cuda", "mps", "cpu"
BERT_MAX_PHRASE_LENGTH = 4
BERT_SIMILARITY_THRESHOLD = 0.3

# ============================================================================
# Translation Settings
# ============================================================================

SOURCE_LANGUAGE = "English"
TARGET_LANGUAGE = "French"

# Translation prompt template
TRANSLATION_PROMPT = (
    "You are a professional translator. Translate the following {source} text to {target}. "
    "Only output the {target} translation, nothing else. "
    "Preserve the meaning and tone of the original text."
)

# ============================================================================
# Directory Configuration
# ============================================================================

# Working directories
INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")
TEMP_DIR = Path("temp")

# Create directories if they don't exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# File Paths
# ============================================================================

# Default input/output files (can be overridden in pipeline)
DEFAULT_INPUT_PPTX = "input/presentation.pptx"
DEFAULT_OUTPUT_PPTX = "output/presentation_translated.pptx"

# Intermediate JSONL files
EXTRACTED_PARAGRAPHS_JSONL = TEMP_DIR / "extracted_paragraphs.jsonl"
TRANSLATED_PARAGRAPHS_JSONL = TEMP_DIR / "translated_paragraphs.jsonl"
ALIGNED_RUNS_JSONL = TEMP_DIR / "aligned_runs.jsonl"

# ============================================================================
# Logging Configuration
# ============================================================================

LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = "translation_pipeline.log"
