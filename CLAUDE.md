# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a modular PowerPoint translation system that uses BERT-based phrase alignment to preserve formatting when translating presentations. The system translates at the paragraph level for better context while redistributing formatting from source to target text using semantic alignment.

**Key capabilities**:
- Translates PowerPoint presentations while preserving text formatting (bold, italic, fonts, colors, hyperlinks)
- Supports multiple translation backends: Local LLMs (HuggingFace), OpenAI GPT, Anthropic Claude
- Uses BERT embeddings for intelligent phrase-level alignment between source and target text
- Handles tables and charts (in addition to standard text)

## Architecture

The system follows a 4-stage pipeline architecture:

```
Extract → Translate → Align → Update
```

### Pipeline Stages

1. **Extraction** (`extract_paragraphs.py`):
   - Extracts paragraphs from PowerPoint with all formatting metadata (runs)
   - Each "run" is a contiguous text segment with consistent formatting
   - Outputs: `temp/extracted_paragraphs.jsonl`

2. **Translation** (`translate_paragraphs.py`):
   - Translates full paragraphs using selected translator backend
   - Uses adapter pattern with `BaseTranslator` interface
   - Outputs: `temp/translated_paragraphs.jsonl`

3. **BERT Alignment** (`apply_alignment.py`):
   - Maps formatting from source runs to target text using phrase-level alignment
   - Uses `PowerPointBERTAligner` from `bert_alignment.py`
   - Generates phrase embeddings and computes similarity scores
   - Outputs: `temp/aligned_runs.jsonl`

4. **PPTX Update** (`update_pptx.py`):
   - Writes aligned runs back to PowerPoint presentation
   - Preserves all formatting properties from alignment
   - Outputs: Translated `.pptx` file

### Key Design Patterns

**Translator Abstraction**: All translators inherit from `BaseTranslator` (in `translators/base.py`) and implement the `translate(text, context)` method. This makes it easy to swap backends or add new ones.

**JSONL Intermediate Format**: Each stage reads/writes JSONL files. This enables:
- Independent execution of each stage for debugging
- Inspection of intermediate results
- Recovery from failures at any stage

**Run-Based Formatting**: PowerPoint text is organized as:
- **Paragraph** → Full text with paragraph-level properties (alignment, bullet)
- **Run** → Substring with consistent formatting (bold, font, color, etc.)

The aligner redistributes source runs to target text by finding semantic phrase matches.

## Running the Pipeline

### Full Pipeline

```bash
# Activate virtual environment
source myenv/bin/activate

# Basic usage (uses config defaults)
python pipeline.py input.pptx output.pptx

# With specific translator
python pipeline.py input.pptx output.pptx --translator openai

# With context (glossary/terminology)
python pipeline.py input.pptx output.pptx --context "Important: Senate = Sénat"

# Verbose mode with intermediate files kept
python pipeline.py input.pptx output.pptx --verbose --keep-intermediate
```

### Individual Stages (for debugging)

```bash
# 1. Extract paragraphs
python extract_paragraphs.py input.pptx temp/extracted.jsonl

# 2. Translate
python translate_paragraphs.py temp/extracted.jsonl temp/translated.jsonl local

# 3. Apply BERT alignment
python apply_alignment.py temp/translated.jsonl temp/aligned.jsonl

# 4. Update PowerPoint
python update_pptx.py input.pptx temp/aligned.jsonl output.pptx
```

## Configuration

All defaults are in `config.py`. Key settings:

**Translator Selection**:
- `TRANSLATOR_TYPE`: "local", "openai", or "anthropic"
- API keys: Set via environment variables or directly in config
- Model names and parameters (temperature, max_tokens)

**BERT Alignment**:
- `BERT_MODEL_NAME`: Default is "sentence-transformers/LaBSE" (multilingual)
- `BERT_DEVICE`: "cpu", "cuda", or "mps"
- `BERT_MAX_PHRASE_LENGTH`: Maximum n-gram size (default: 4)
- `BERT_SIMILARITY_THRESHOLD`: Minimum similarity for alignment (default: 0.3)

**Languages**:
- `SOURCE_LANGUAGE`: Default "English"
- `TARGET_LANGUAGE`: Default "French"

## Data Flow and Formats

### JSONL Structure

Each JSONL file contains one JSON object per line. Structure evolves through pipeline:

**Extracted** (after Stage 1):
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
    {"run_index": 0, "text": "Employees with an ", "bold": false, "font": "Arial", ...},
    {"run_index": 1, "text": "invisible", "bold": true, "font": "Arial", ...}
  ]
}
```

**Translated** (after Stage 2) - adds:
```json
{
  ...,
  "translated_text": "Les employés ayant un handicap invisible"
}
```

**Aligned** (after Stage 3) - adds:
```json
{
  ...,
  "aligned_runs": [
    {"text": "Les employés ayant un ", "bold": false, ...},
    {"text": "handicap invisible", "bold": true, ...}
  ]
}
```

## BERT Alignment Details

The `PowerPointBERTAligner` class (`bert_alignment.py`) performs phrase-aware alignment:

1. **Phrase Embedding Generation** (`get_phrase_embeddings`):
   - Generates embeddings for all words and n-grams up to `max_phrase_length`
   - Uses multilingual BERT for cross-lingual semantic similarity

2. **Similarity Computation** (`compute_phrase_similarity`):
   - Combines multiple signals with weights:
     - BERT cosine similarity (30%)
     - Semantic mapping bonus from phrase dictionary (40%)
     - Length similarity (15%)
     - Character overlap (15%)

3. **Greedy Alignment** (`find_optimal_alignments`):
   - Iteratively selects highest-scoring phrase pairs
   - Prevents overlapping alignments using position tracking
   - Only accepts alignments above similarity threshold

4. **Format Mapping** (`align_paragraph_runs`):
   - Maps source run formatting to aligned target phrases
   - Handles partial overlaps by splitting runs

**Important**: The `phrase_mappings` dictionary in `PowerPointBERTAligner.__init__()` contains hand-crafted English-French phrase pairs. Add entries here to improve alignment quality for specific terminology.

## Adding a New Translator

1. Create `translators/my_translator.py`:
```python
from .base import BaseTranslator

class MyTranslator(BaseTranslator):
    def __init__(self, api_key, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key

    def translate(self, text, context=None):
        # Your translation logic
        return translated_text
```

2. Update `translators/__init__.py` to export your class

3. Add configuration parameters to `config.py`

4. Update `translate_paragraphs.py` to instantiate your translator in the `__init__` method

## Virtual Environment

Python environment is in `myenv/`. Key packages:
- `torch>=2.0.0` - PyTorch for BERT
- `transformers>=4.30.0` - HuggingFace transformers
- `python-pptx>=0.6.21` - PowerPoint manipulation
- `openai>=1.0.0` - OpenAI API (optional)
- `anthropic>=0.21.0` - Anthropic API (optional)

Activate: `source myenv/bin/activate`

## Troubleshooting

### Memory Issues
- Reduce `BERT_MAX_PHRASE_LENGTH` in config (fewer n-grams = less memory)
- Set `BERT_DEVICE = "cpu"` instead of GPU
- Use API-based translator instead of local LLM

### Poor Alignment Quality
- Increase `BERT_SIMILARITY_THRESHOLD` (more conservative matching)
- Add phrase mappings to `phrase_mappings` dict in `bert_alignment.py`
- Check BERT model - "sentence-transformers/LaBSE" is better for multilingual than "bert-base-multilingual-cased"

### API Rate Limits
- Translators call API once per paragraph - reduce presentation size
- Add retry logic in translator implementations
- Switch to local model for high-volume work

## Known Limitations

- Theme colors are extracted but not fully restored (only RGB colors work reliably)
- Chart translation is basic - may not handle all chart types
- Tables are supported but complex merged cells may have issues
- No sentence-level splitting within paragraphs (entire paragraph translated as one unit)

---

## Project Progress Log

### 2025-10-23: Glossary System & API Planning

**✅ Completed Today:**

1. **Terminology Glossary System** - Full implementation
   - Created `glossary.py` with complete glossary management
   - Supports JSON, CSV, and dictionary formats
   - Context-aware term disambiguation
   - Priority-based matching for overlapping terms
   - Auto-generates BERT phrase mappings from glossary
   - Translation verification system

2. **Glossary Integration** - Throughout pipeline
   - Integrated into `translate_paragraphs.py` (auto-injects glossary into LLM prompts)
   - Integrated into `translate_content.py` (charts & tables)
   - Integrated into `apply_alignment.py` (BERT phrase mappings)
   - Integrated into `apply_table_alignment.py` (BERT for tables)

3. **Sample Glossary & Documentation**
   - Created `glossary.json` with 16 Canadian government & disability terms
   - Created `GLOSSARY_USAGE.md` - comprehensive usage guide
   - Created `test_glossary_integration.py` - demonstration script
   - Created `test_pipeline_with_glossary.py` - full pipeline test

4. **Table BERT Alignment** - Completed earlier
   - `apply_table_alignment.py` applies BERT to table cells
   - Preserves formatting within cells (bold, italic, etc.)
   - Integrated into 9-step pipeline

**📋 How Glossary Works:**
- **Translation Stage:** Glossary → LLM prompts → Consistent terms
- **Alignment Stage:** Glossary → BERT mappings → Better formatting match
- **Result:** "Senate" always translates to "Sénat" with proper formatting

**🎯 Next Steps Planned:**

### Phase 1: Local API Development (Next 1-2 weeks)
**Goal:** Enable testing via web interface

**Week 1 Tasks:**
1. Build FastAPI server with endpoints:
   - POST /api/translate - Upload PPTX, return job_id
   - GET /api/status/{job_id} - Check progress
   - GET /api/download/{job_id} - Get translated file
2. Implement Redis job queue for background processing
3. Create simple HTML upload frontend
4. Set up ngrok tunnel for public access
5. Test with 2-3 users

**Architecture - Local Testing:**
```
User Browser → ngrok URL → Your Laptop (FastAPI + GPU + Redis)
Cost: $0
Capacity: 1-3 concurrent users
```

### Phase 2: Cloud Deployment (Week 2-3)
**Goal:** Scalable cloud deployment with on-demand GPU

**Deployment Options Evaluated:**

**Option A: Cloud GPU On-Demand** (~$30-50/month)
```
User → Cloud API (Railway $5/month)
     → Redis Queue (Free tier)
     → GPU Worker (RunPod $0.40/hour, auto-shutdown when idle)
```
- Only pay for GPU when translating
- Auto-scales based on demand
- Good for testing phase (5-20 users)

**Option B: Hybrid Cloud** (~$20-50/month)
```
User → Cloud API (Railway $5/month)
     → OpenAI/Anthropic API ($0.15 per presentation)
```
- No GPU needed (cheaper for low volume)
- Better translation quality
- Instant startup (no model loading)
- Recommended for initial testing

**Decision:** Start with Local (Phase 1), then migrate to Hybrid (Option B) based on usage

### Phase 3: Production Features (Future)
**Priority based on feedback:**
1. Model caching (10x speed improvement)
2. Batch translation
3. Error handling & validation
4. Web UI with real-time progress
5. Monitoring & analytics

**🔧 Technical Flexibility Confirmed:**
- ✅ Current architecture supports easy LLM switching (local ↔ OpenAI ↔ Anthropic)
- ✅ Just change `TRANSLATOR_TYPE` in config - no code changes needed
- ✅ Glossary works with any translator backend

**📊 Current System Status:**
- ✅ Complete 9-step pipeline working
- ✅ Formatting preservation (paragraphs + tables)
- ✅ Terminology consistency (glossary system)
- ✅ Multi-translator support (local/OpenAI/Anthropic)
- ⏳ API layer - planned next
- ⏳ Cloud deployment - planned after API

**Next Session Goal:** Build local FastAPI server for testing
