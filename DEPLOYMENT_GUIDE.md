# PowerPoint Translation App - Deployment Guide

## 📋 Project Overview

A production-ready PowerPoint translation application with AI-powered translation and formatting preservation.

**Live URL**: https://cleantranslate.vercel.app

**Developer**: Jason Hao (haomengqi12138@gmail.com)

---

## 🏗️ Architecture

### Three-Tier Deployment

```
Frontend (Vercel) → Backend API (Railway) → GPU Translation (RunPod)
```

| Component | Platform | Purpose | Auto-Deploy |
|-----------|----------|---------|-------------|
| **Frontend** | Vercel | User interface, file upload | ✅ Yes (on git push) |
| **Backend API** | Railway | Request routing, job management | ✅ Yes (on git push) |
| **GPU Workers** | RunPod Serverless | AI translation (8B/14B models) | ❌ Manual rebuild |

---

## 🌐 Deployment URLs

- **Frontend**: https://cleantranslate.vercel.app
- **Backend API**: https://translationapp2ed-production.up.railway.app
- **RunPod Endpoint**: `io6lj6wjt80mqe`

---

## ✨ Features

### Translation
- ✅ Multiple AI models: 8B (fast), 14B (accurate)
- ✅ Preserves PowerPoint formatting (bold, italic, fonts, colors)
- ✅ BERT-based phrase alignment for accuracy
- ✅ Supports tables and charts

### User Experience
- ✅ Real-time progress tracking with milestones
- ✅ Translation preview (source → target pairs)
- ✅ Custom glossary with download/upload
- ✅ Cancel translation mid-process
- ✅ Queue status display

### Developer Features
- ✅ Version control display (v1.0.1)
- ✅ Contact information for support
- ✅ Comprehensive error logging

---

## 🔄 Update Workflow

### Frontend Changes (HTML/CSS/JavaScript)

**Files**: `frontend/index.html`

**Process**:
```bash
# 1. Make changes to frontend/index.html
# 2. Commit and push
git add frontend/index.html
git commit -m "Your change description"
git push

# 3. Vercel auto-deploys in ~1 minute
# No manual action needed!
```

**Applies to**: UI changes, glossary features, styling

---

### Backend Changes (API/Logic)

**Files**: `api.py`, `config.py`

**Process**:
```bash
# 1. Make changes
# 2. Commit and push
git add api.py config.py
git commit -m "Your change description"
git push

# 3. Railway auto-deploys in ~1-2 minutes
# No manual action needed!
```

**Applies to**: Progress tracking, error handling, job management

---

### RunPod Changes (Translation Logic)

**Files**: `pipeline.py`, `translate_*.py`, `bert_alignment.py`

**Process**:
```bash
# 1. Make changes and commit
git add pipeline.py translate_paragraphs.py
git commit -m "Your change description"
git push

# 2. Rebuild Docker image (v9 example)
cd /Users/jasonhao/Desktop/fast_align_test/translationAPP_2ed

docker buildx build --platform linux/amd64 \
  -f scripts/Dockerfile.runpod \
  -t nejoasfa/ppt-translator:v9 \
  -t nejoasfa/ppt-translator:latest \
  .

# 3. Push to Docker Hub (~5 minutes)
docker push nejoasfa/ppt-translator:v9
docker push nejoasfa/ppt-translator:latest

# 4. Update RunPod (choose one):

# Option A: Manual redeploy (30 seconds, recommended)
# - Go to https://www.runpod.io/console/serverless
# - Find endpoint io6lj6wjt80mqe
# - Click "Redeploy"

# Option B: Natural rollover (10-15 minutes)
# - Wait for old workers to idle out
# - New workers automatically use latest image
```

**Applies to**: Model changes, translation logic, alignment improvements

---

## 📦 Docker Image Versioning

### Current Image
- **Latest**: `nejoasfa/ppt-translator:latest`
- **Version**: `nejoasfa/ppt-translator:v9`
- **Size**: ~7.8 GB

### Version History
- **v6**: Initial deployment with 8B model
- **v7**: Added 14B model support (had bugs)
- **v8**: Fixed GPU memory sharing
- **v9**: Added translation pairs collection

### Tagging Strategy
Always use dual tags for version control:
```bash
-t nejoasfa/ppt-translator:v9      # Specific version (rollback capability)
-t nejoasfa/ppt-translator:latest  # Always newest (easy deployment)
```

**Storage**: Only ONE image is stored (tags are just pointers)

---

## 🔐 Environment Variables

### Location
`.env` file (git-ignored for security)

### Required Variables
```bash
# OpenAI (optional)
OPENAI_API_KEY=sk-proj-...

# Anthropic (optional)
ANTHROPIC_API_KEY=sk-ant-...

# RunPod (required)
RUNPOD_ENDPOINT_ID=io6lj6wjt80mqe
RUNPOD_API_KEY=rpa_3O2QGMN26HIIKM3L345AXOB3MH3XWX0N14KZX9TJ13ggys
USE_RUNPOD=true
```

### Template
See `.env.example` for template

---

## 🔧 RunPod Configuration

### Endpoint Settings
- **Endpoint ID**: `io6lj6wjt80mqe`
- **Container Image**: `nejoasfa/ppt-translator:latest`
- **Container Disk**: 80 GB (for model storage)
- **GPU**: RTX 3090 24GB or better
- **Max Workers**: 1-3 (based on budget)

### Why 80GB Disk?
- Docker image: ~8 GB
- Qwen3-8B model: ~16 GB
- Qwen3-14B model: ~28 GB
- LaBSE BERT: ~2 GB
- Temp files: ~5 GB
- **Total**: ~60 GB (80 GB provides buffer)

---

## 📞 Support

**Developer**: Jason Hao  
**Email**: haomengqi12138@gmail.com  
**Website**: https://cleantranslate.vercel.app

---

**Last Updated**: November 18, 2025  
**Maintained By**: Jason Hao
