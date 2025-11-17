# PowerPoint Translation Pipeline with BERT Alignment

A modern, modular PowerPoint translation system that uses BERT-based phrase alignment to preserve formatting when translating presentations. Supports both local LLMs and API-based translation services.

## Features

- **Phrase-aware translation**: Translates at paragraph level for better context and quality
- **BERT alignment**: Intelligently redistributes formatting from source to target text
- **Multiple translator backends**: Local LLMs (HuggingFace), OpenAI GPT, Anthropic Claude
- **Format preservation**: Maintains bold, italic, underline, fonts, colors, hyperlinks, superscript/subscript
- **Modular architecture**: Each stage can be run independently or as a complete pipeline
- **Extensible**: Easy to add new translator backends or alignment strategies

## Architecture

The pipeline consists of 4 main stages:

```
1. Extraction      →  2. Translation  →  3. BERT Alignment  →  4. PPTX Update
   (paragraph-level)    (with context)      (format mapping)      (write back)
```

### Pipeline Flow

1. **Extraction** (`extract_paragraphs.py`):
   - Extracts paragraphs from PowerPoint with all formatting metadata
   - Groups runs within paragraphs
   - Outputs: `extracted_paragraphs.jsonl`

2. **Translation** (`translate_paragraphs.py`):
   - Translates full paragraphs using selected translator
   - Supports context injection (e.g., glossary terms)
   - Outputs: `translated_paragraphs.jsonl`

3. **BERT Alignment** (`apply_alignment.py`):
   - Aligns source and target text at phrase level
   - Maps formatting from source runs to target text
   - Outputs: `aligned_runs.jsonl`

4. **PPTX Update** (`update_pptx.py`):
   - Writes aligned runs back to PowerPoint
   - Preserves all formatting properties
   - Outputs: Translated `.pptx` file

## Installation

### Prerequisites

- Python 3.8+
- PyTorch
- Transformers (HuggingFace)
- python-pptx

### Install Dependencies

```bash
pip install torch transformers python-pptx
```

### Optional: API Clients

For OpenAI:
```bash
pip install openai
```

For Anthropic:
```bash
pip install anthropic
```

## Quick Start

### Basic Usage

```bash
python pipeline.py input.pptx output.pptx
```

### With OpenAI Translator

```bash
export OPENAI_API_KEY="sk-..."
python pipeline.py input.pptx output.pptx --translator openai
```

### With Anthropic Claude

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python pipeline.py input.pptx output.pptx --translator anthropic
```

### With Context (Glossary)

```bash
python pipeline.py input.pptx output.pptx --context "Important: Senate = Sénat, Prime Minister = Premier ministre"
```

## Configuration

Edit `config.py` to set default options:

```python
# Translator type: "local", "openai", "anthropic"
TRANSLATOR_TYPE = "local"

# Local model settings
LOCAL_MODEL_NAME = "Qwen/Qwen3-8B"
LOCAL_DEVICE = "auto"  # auto, cuda, mps, cpu

# OpenAI settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o-mini"

# Anthropic settings
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"

# BERT alignment settings
BERT_MODEL_NAME = "bert-base-multilingual-cased"
BERT_DEVICE = "cpu"
BERT_MAX_PHRASE_LENGTH = 4
BERT_SIMILARITY_THRESHOLD = 0.3
```

## Command-Line Options

```
python pipeline.py [-h] [--translator {local,openai,anthropic}]
                        [--context CONTEXT] [--keep-intermediate]
                        [--verbose] input output

Positional arguments:
  input                 Input PowerPoint file (.pptx)
  output                Output PowerPoint file (.pptx)

Optional arguments:
  --translator          Translator type (default: from config)
  --context             Optional context for translation
  --keep-intermediate   Keep intermediate JSONL files
  --verbose             Enable verbose logging
```

## Running Individual Stages

You can run each stage independently for debugging or custom workflows:

### Extract Paragraphs

```bash
python extract_paragraphs.py input.pptx extracted.jsonl
```

### Translate Paragraphs

```bash
python translate_paragraphs.py extracted.jsonl translated.jsonl local
```

### Apply BERT Alignment

```bash
python apply_alignment.py translated.jsonl aligned.jsonl
```

### Update PowerPoint

```bash
python update_pptx.py input.pptx aligned.jsonl output.pptx
```

## File Structure

```
translationAPP_2ed/
├── config.py                  # Configuration settings
├── pipeline.py                # Main pipeline orchestrator
├── extract_paragraphs.py      # Paragraph extraction
├── translate_paragraphs.py    # Translation with multiple backends
├── apply_alignment.py         # BERT alignment application
├── update_pptx.py            # PowerPoint update
├── bert_alignment.py          # BERT aligner implementation
├── translators/               # Translator implementations
│   ├── __init__.py
│   ├── base.py               # Base translator interface
│   ├── local_llm.py          # Local HuggingFace models
│   ├── openai_translator.py  # OpenAI GPT
│   └── anthropic_translator.py # Anthropic Claude
├── input/                     # Input files directory
├── output/                    # Output files directory
├── temp/                      # Intermediate JSONL files
└── README.md                  # This file
```

## Data Format

### Extracted Paragraphs (JSONL)

```json
{
  "slide_index": 0,
  "shape_index": 1,
  "paragraph_index": 0,
  "text": "Employees with an invisible disability",
  "alignment": "left",
  "level": 0,
  "is_bullet": false,
  "runs": [
    {
      "run_index": 0,
      "text": "Employees with an ",
      "font": "Arial",
      "size": 12.0,
      "bold": false,
      "italic": false,
      "underline": false,
      "color": "#000000",
      "superscript": false,
      "subscript": false,
      "hyperlink": null
    },
    {
      "run_index": 1,
      "text": "invisible",
      "font": "Arial",
      "size": 12.0,
      "bold": true,
      ...
    }
  ]
}
```

### Translated Paragraphs (JSONL)

Same as extracted, with added field:
```json
{
  ...
  "translated_text": "Les employés ayant un handicap invisible"
}
```

### Aligned Runs (JSONL)

Same as translated, with added field:
```json
{
  ...
  "aligned_runs": [
    {
      "text": "Les employés ayant un ",
      "bold": false,
      ...
    },
    {
      "text": "handicap invisible",
      "bold": true,
      ...
    }
  ]
}
```

## Adding New Translators

To add a new translation backend:

1. Create a new file in `translators/` (e.g., `my_translator.py`)
2. Inherit from `BaseTranslator`
3. Implement the `translate()` method
4. Update `translators/__init__.py`
5. Add configuration in `config.py`
6. Update `translate_paragraphs.py` to instantiate your translator

Example:

```python
# translators/my_translator.py
from .base import BaseTranslator

class MyTranslator(BaseTranslator):
    def __init__(self, api_key, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key

    def translate(self, text, context=None):
        # Your translation logic here
        return translated_text
```

## Troubleshooting

### Out of Memory Error

- Reduce `BERT_MAX_PHRASE_LENGTH` in config
- Use `BERT_DEVICE = "cpu"` instead of GPU
- Use smaller local model or switch to API

### Poor Alignment Quality

- Increase `BERT_SIMILARITY_THRESHOLD` (e.g., 0.4)
- Add more phrase mappings in `bert_alignment.py`
- Use longer `BERT_MAX_PHRASE_LENGTH` for better phrase detection

### API Rate Limits

- Add retry logic in translator implementations
- Use batch translation where supported
- Switch to local model for high-volume work

## Limitations

- Theme colors are extracted but not fully restored (only RGB colors work)
- Complex chart translations not yet supported
- Table translations not yet implemented (only text blocks)
- Sentence-level splitting within paragraphs not implemented

## Future Improvements

- [ ] Add table support
- [ ] Implement sentence-level splitting for better alignment
- [ ] Add RAG/glossary integration
- [ ] Support more languages beyond English-French
- [ ] Add progress bars for long-running operations
- [ ] Implement caching for repeated translations
- [ ] Add unit tests

## License

MIT License

## Credits

- BERT alignment adapted from `phrase_aware_bert_aligner.py`
- Built with python-pptx, transformers, and PyTorch
