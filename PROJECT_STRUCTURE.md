# Project Structure

Clean, production-ready organization for the PowerPoint Translation App.

## 📁 Directory Structure

```
pptx-translator/
│
├── 📄 Core Application Files (Root Level)
│   ├── api.py                      # FastAPI server (entry point for Railway)
│   ├── config.py                   # Configuration settings
│   ├── pipeline.py                 # Main translation pipeline orchestrator
│   ├── glossary.py                 # Terminology glossary system
│   ├── bert_alignment.py           # BERT-based format alignment
│   ├── extract_content.py          # Extract paragraphs/tables/charts from PPTX
│   ├── translate_paragraphs.py     # Translate paragraph content
│   ├── translate_content.py        # Translate charts and tables
│   ├── apply_alignment.py          # Apply BERT alignment to paragraphs
│   ├── apply_table_alignment.py    # Apply BERT alignment to tables
│   ├── build_slide_context.py      # Build context for better translation
│   ├── update_pptx.py              # Update PowerPoint with translations
│   └── runpod_handler.py           # RunPod serverless handler
│
├── 📦 Deployment Configuration
│   ├── requirements.txt            # Python dependencies
│   ├── railway.json                # Railway deployment config
│   ├── vercel.json                 # Vercel deployment config
│   ├── .gitignore                  # Git ignore rules
│   └── .env.example                # Environment variables template
│
├── 📖 Documentation
│   ├── README.md                   # Project overview & quick start
│   ├── DEPLOY_CHECKLIST.md         # Step-by-step deployment guide
│   ├── DEPLOYMENT_GUIDE.md         # Comprehensive deployment docs
│   ├── FRONTEND_SETUP.md           # Frontend/backend integration
│   ├── CLAUDE.md                   # Development guide & architecture
│   ├── PROJECT_STRUCTURE.md        # This file!
│   └── API_README.md               # API documentation
│
├── 🖥️ Frontend (Web UI)
│   frontend/
│   └── index.html                  # Single-page web application
│
├── 🔧 Translation Backends
│   translators/
│   ├── __init__.py                 # Package initialization
│   ├── base.py                     # Base translator interface
│   ├── local_llm.py                # Local LLM (Qwen, Llama, etc.)
│   ├── openai.py                   # OpenAI GPT translator
│   └── anthropic.py                # Anthropic Claude translator
│
├── 📜 Scripts & Utilities
│   scripts/
│   ├── runpod_client.py            # RunPod API client for testing
│   ├── deploy_runpod.sh            # Deploy Docker image to RunPod
│   ├── start_api_runpod.sh         # Start local API with RunPod backend
│   ├── start_api_local.sh          # Start local API with local LLM
│   ├── run_pipeline.sh             # Run translation pipeline CLI
│   └── Dockerfile.runpod           # Docker image for RunPod serverless
│
├── 🧪 Tests
│   tests/
│   ├── test_pipeline_with_glossary.py  # Full pipeline test
│   ├── test_glossary_integration.py    # Glossary system test
│   └── test_workflow.py                # Basic workflow test
│
├── 📊 Data & Configuration
│   data/
│   ├── glossary.json               # Default terminology glossary
│   └── sample.pptx                 # Sample input file (optional)
│
├── 📚 Additional Documentation
│   docs/
│   ├── GLOSSARY_USAGE.md           # How to use glossaries
│   ├── RUNPOD_DEPLOYMENT.md        # RunPod serverless guide
│   └── PRODUCTION_READINESS.md     # Production deployment analysis
│
└── 🗂️ Runtime Directories (Created Automatically)
    ├── temp/                       # Temporary processing files
    ├── uploads/                    # User-uploaded files (API)
    ├── output/                     # Translated output files
    └── logs/                       # Application logs
```

## 🔗 Key File Relationships

### Import Hierarchy

```
api.py
  └─ pipeline.py
      ├─ glossary.py
      ├─ extract_content.py
      ├─ translate_paragraphs.py
      │   └─ translators/ (local_llm, openai, anthropic)
      ├─ translate_content.py
      │   └─ translators/
      ├─ apply_alignment.py
      │   └─ bert_alignment.py
      ├─ apply_table_alignment.py
      │   └─ bert_alignment.py
      ├─ build_slide_context.py
      └─ update_pptx.py
```

### Deployment Entry Points

- **Railway (Web API):** `api.py`
- **RunPod (Serverless):** `runpod_handler.py`
- **Local CLI:** `pipeline.py`

## 📝 File Descriptions

### Core Application

| File | Purpose | Dependencies |
|------|---------|--------------|
| `api.py` | FastAPI web server, handles HTTP requests, background jobs | All pipeline modules |
| `pipeline.py` | Orchestrates the 9-step translation pipeline | All core modules |
| `glossary.py` | Terminology management with BERT integration | transformers |
| `bert_alignment.py` | Phrase-level formatting alignment using BERT | transformers, torch |

### Translation Pipeline Steps

| Step | File | Input | Output |
|------|------|-------|--------|
| 1 | `extract_content.py` | PPTX file | Paragraphs, tables, charts (JSONL) |
| 2 | `translate_paragraphs.py` | Paragraphs | Translated paragraphs |
| 3 | `apply_alignment.py` | Translated paragraphs | Aligned runs with formatting |
| 4 | `build_slide_context.py` | Aligned paragraphs | Slide context |
| 5-6 | `translate_content.py` | Charts, tables | Translated charts/tables |
| 7 | `apply_table_alignment.py` | Translated tables | Aligned table cells |
| 8 | `pipeline.py` (merge step) | All content | Merged JSONL |
| 9 | `update_pptx.py` | Merged JSONL + original PPTX | Translated PPTX |

### Deployment Scripts

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `start_api_runpod.sh` | Start local API with RunPod backend | Local development/testing |
| `start_api_local.sh` | Start local API with local LLM | Offline development |
| `deploy_runpod.sh` | Build & push Docker image | Deploy new RunPod version |
| `runpod_client.py` | Test RunPod endpoint | Verify RunPod deployment |

## 🌐 Deployment Modes

### 1. Local Development

```bash
./scripts/start_api_local.sh
# Visit: http://localhost:8000
```

**Uses:**
- Local LLM (Qwen)
- BERT on CPU/GPU
- Glossary from `data/glossary.json`

### 2. Local with RunPod Backend

```bash
./scripts/start_api_runpod.sh
# Visit: http://localhost:8000
```

**Uses:**
- FastAPI locally
- RunPod for GPU translation
- Same frontend

### 3. Full Production (Railway + Vercel)

```
Frontend: Vercel (Static HTML)
    ↓
Backend: Railway (FastAPI)
    ↓
GPU: RunPod (Serverless)
```

**See:** `DEPLOY_CHECKLIST.md` for steps

## 🔧 Configuration Files

| File | Purpose | Required For |
|------|---------|--------------|
| `requirements.txt` | Python dependencies | All deployments |
| `railway.json` | Railway build config | Railway deployment |
| `vercel.json` | Vercel routing config | Vercel deployment |
| `.env` (not in Git) | Secret keys | All deployments |
| `config.py` | Application settings | All modes |

## 🚀 Getting Started

**For Users:**
1. Visit the deployed site (Vercel URL)
2. Upload PowerPoint
3. Download translated version

**For Developers:**
1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run locally: `./scripts/start_api_local.sh`
4. Deploy: Follow `DEPLOY_CHECKLIST.md`

**For Contributors:**
1. Read `CLAUDE.md` for architecture details
2. Check `docs/` for specific guides
3. Run tests: `python tests/test_pipeline_with_glossary.py`
4. Submit PR

## 📊 Dependencies

### Python Packages (see `requirements.txt`)

**Core:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `python-pptx` - PowerPoint manipulation

**AI/ML:**
- `torch` - PyTorch for BERT
- `transformers` - Hugging Face models
- `accelerate` - Model optimization

**Translation APIs:**
- `openai` - OpenAI GPT
- `anthropic` - Claude API
- `runpod` - RunPod serverless

**Utilities:**
- `tqdm` - Progress bars
- `python-multipart` - File uploads

### External Services

- **RunPod:** GPU inference ($0.30-0.50 per translation)
- **Railway:** Backend hosting (FREE tier available)
- **Vercel:** Frontend hosting (FREE tier available)

## 🧹 Maintenance

### Updating Dependencies

```bash
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt  # Update versions
```

### Cleaning Temporary Files

```bash
rm -rf temp/ uploads/ output/ logs/
rm -rf __pycache__/ */__pycache__/
```

### Rebuilding RunPod Image

```bash
./scripts/deploy_runpod.sh
# Follow prompts to build & push new version
```

## 📄 License

MIT License - See LICENSE file

---

**Last Updated:** 2025-11-17
**Version:** 1.0.0
**Maintained by:** [Your Name]
