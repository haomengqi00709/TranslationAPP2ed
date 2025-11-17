# PowerPoint Translation App

AI-powered PowerPoint translator that preserves formatting, charts, and tables. Translate presentations from English to French while maintaining all visual styling.

🌐 **Deploy to the web:** See [DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md)

## ✨ Features

- 📄 **Format Preservation** - Maintains bold, italic, fonts, colors, and hyperlinks
- 📊 **Chart & Table Support** - Translates all content types
- 🎯 **Custom Glossary** - Add domain-specific terminology via web UI
- 🧠 **BERT Alignment** - Intelligent phrase-level formatting mapping
- ⚡ **GPU-Accelerated** - Fast translation using RunPod serverless
- 🌍 **Multiple Backends** - Local LLM, OpenAI, or Anthropic

## 🚀 Quick Start

### Local Development

```bash
# Activate environment
source myenv/bin/activate

# Start the web interface
./start_api_runpod.sh  # Uses RunPod backend (recommended)
# OR
./start_api_local.sh   # Uses local LLM

# Open browser
open http://localhost:8000
```

### Deploy to Production (Railway + Vercel)

See [DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md) for step-by-step deployment.

**Estimated cost:** FREE for low usage, ~$0.30-0.50 per translation at scale

## Project Structure

```
translationAPP_2ed/
├── Core Pipeline Files (10 scripts)
│   ├── extract_content.py              # Extract paragraphs, tables, charts
│   ├── translate_paragraphs.py         # Translate paragraphs
│   ├── translate_content.py            # Translate charts/tables
│   ├── apply_alignment.py              # BERT align paragraphs
│   ├── apply_table_alignment.py        # BERT align tables
│   ├── build_slide_context.py          # Build slide context
│   ├── update_pptx.py                  # Update PowerPoint
│   ├── bert_alignment.py               # BERT aligner core
│   ├── glossary.py                     # Glossary system
│   └── pipeline.py                     # Main pipeline
│
├── Configuration
│   ├── config.py                       # Settings
│   ├── glossary.json                   # Sample glossary
│   └── requirements.txt                # Dependencies
│
├── docs/                               # Documentation
│   ├── README.md                       # Detailed readme
│   ├── GLOSSARY_USAGE.md              # Glossary guide
│   ├── PRODUCTION_READINESS.md        # Production analysis
│   └── ...
│
├── tests/                              # Test scripts
│   ├── test_pipeline_with_glossary.py # Full pipeline test
│   ├── test_glossary_integration.py   # Glossary demo
│   └── test_workflow.py               # Basic test
│
├── translators/                        # Translator backends
├── slides/                             # Input files
├── output/                             # Output files
├── temp/                               # Processing temp files
└── logs/                               # Log files

└── CLAUDE.md                           # 👈 START HERE - Project overview
```

## Key Features

✅ **Formatting Preservation** - Bold, italic, fonts, colors preserved
✅ **Table Support** - Full BERT alignment for table cells
✅ **Glossary System** - Consistent terminology across document
✅ **Multi-Translator** - Local LLM, OpenAI, Anthropic
✅ **9-Step Pipeline** - Extract → Translate → Align → Update

## 📖 Documentation

- **[DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md)** - 📌 Deploy to Railway + Vercel (recommended!)
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Comprehensive deployment guide
- **[FRONTEND_SETUP.md](FRONTEND_SETUP.md)** - Connect frontend to backend
- **[CLAUDE.md](CLAUDE.md)** - Complete project overview and architecture
- **[docs/GLOSSARY_USAGE.md](docs/GLOSSARY_USAGE.md)** - How to use glossaries
- **[docs/RUNPOD_DEPLOYMENT.md](docs/RUNPOD_DEPLOYMENT.md)** - RunPod serverless guide

## 🏗️ Architecture

```
User Browser (Vercel Frontend)
    ↓
FastAPI Server (Railway Backend)
    ↓
RunPod Serverless (GPU Translation)
```

**9-Step Translation Pipeline:**
1. Extract paragraphs, tables, charts from PowerPoint
2. Translate paragraphs using LLM with glossary context
3. Align paragraph formatting using BERT embeddings
4. Build slide context for better translation
5. Translate charts
6. Translate tables
7. Align table formatting
8. Merge all content
9. Update PowerPoint with translations

## 💰 Deployment Costs

| Service | Free Tier | Cost at Scale |
|---------|-----------|---------------|
| **Vercel** (Frontend) | 100GB/month | FREE for most use cases |
| **Railway** (Backend) | $5 credit/month | ~$0 if under 500 hours |
| **RunPod** (GPU) | Pay-per-use | ~$0.30-0.50 per translation |

**Total:** ~$0 for 100 translations/month (well within free tiers!)

## 🎯 Next Steps

1. **Try locally:** Run `./start_api_runpod.sh` and visit http://localhost:8000
2. **Deploy online:** Follow [DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md)
3. **Customize:** Edit `config.py` or `glossary.json`
4. **Learn more:** See [CLAUDE.md](CLAUDE.md) for architecture details
