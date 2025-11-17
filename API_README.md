# Translation API - Quick Start

RESTful API for translating PowerPoint presentations with formatting preservation.

## 🚀 Quick Start (Docker)

```bash
# 1. Build and run
docker-compose up --build

# 2. Open web interface
open http://localhost:8000

# 3. Upload a PowerPoint file and translate!
```

## 🚀 Quick Start (Local Python)

```bash
# 1. Activate environment
source myenv/bin/activate

# 2. Install API dependencies
pip install fastapi uvicorn python-multipart

# 3. Run API server
python api.py

# 4. Open web interface
open http://localhost:8000
```

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web UI |
| `/api/translate` | POST | Upload and translate PowerPoint |
| `/api/status/{job_id}` | GET | Check job status |
| `/api/download/{job_id}` | GET | Download translated file |
| `/api/glossary` | GET | Get terminology glossary |
| `/health` | GET | Health check |

---

## 🧪 Test with curl

```bash
# 1. Upload file
curl -X POST http://localhost:8000/api/translate \
  -F "file=@slides/presentation.pptx" \
  -F "translator_type=local"

# Response: {"job_id": "abc-123", ...}

# 2. Check status
curl http://localhost:8000/api/status/abc-123

# 3. Download result
curl -O -J http://localhost:8000/api/download/abc-123
```

---

## 🐍 Python Client

```python
import requests

# Upload
with open("presentation.pptx", "rb") as f:
    resp = requests.post(
        "http://localhost:8000/api/translate",
        files={"file": f}
    )

job_id = resp.json()["job_id"]

# Check status
status = requests.get(f"http://localhost:8000/api/status/{job_id}").json()

# Download when completed
if status["status"] == "completed":
    result = requests.get(f"http://localhost:8000/api/download/{job_id}")
    with open("translated.pptx", "wb") as f:
        f.write(result.content)
```

---

## ⚙️ Configuration

### Translation Options

- `translator_type`: `local` (free, GPU), `openai` (paid, fast), `anthropic` (paid, quality)
- `use_glossary`: `true` (recommended) or `false`
- `context`: Optional instructions (e.g., "Use formal tone")

### Environment Variables

Create `.env` file:

```bash
TRANSLATOR_TYPE=local
BERT_DEVICE=cpu
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

---

## 🐳 Docker Deployment

### Basic

```bash
docker-compose up -d
```

### With GPU (for local LLM)

Uncomment GPU section in `docker-compose.yml`, then:

```bash
docker-compose up --build
```

### Check logs

```bash
docker-compose logs -f
```

---

## 📚 Documentation

- **Complete API Guide**: `docs/API_GUIDE.md`
- **Project Overview**: `CLAUDE.md`
- **Glossary Usage**: `docs/GLOSSARY_USAGE.md`

---

## 🔧 Troubleshooting

### Port already in use

```bash
# Change port in docker-compose.yml
ports:
  - "8080:8000"  # Use 8080 instead
```

### Out of memory

```bash
# Use CPU for BERT
export BERT_DEVICE=cpu

# Or use cloud translator instead of local
export TRANSLATOR_TYPE=openai
```

### Missing dependencies

```bash
# Rebuild without cache
docker-compose build --no-cache
```

---

## 🚀 Production Deployment

### Option 1: Local + ngrok (Free)

```bash
# Terminal 1: Run API
docker-compose up

# Terminal 2: Expose via ngrok
ngrok http 8000
```

Share the ngrok URL: `https://xxxx.ngrok-free.app`

### Option 2: Cloud GPU (Paid)

Deploy to RunPod, Vast.ai, or Lambda Labs:

```bash
ssh user@gpu-instance
git clone <repo>
cd translationAPP_2ed
docker-compose up -d
```

Cost: ~$0.30-1.00/hour when running

### Option 3: Hybrid Cloud (API + Local)

Use OpenAI/Anthropic for translation, run BERT locally:

```bash
export TRANSLATOR_TYPE=openai
docker-compose up
```

Cost: ~$0.01-0.05 per slide

---

## 📊 Features

✅ Text, tables, and charts translation
✅ Formatting preservation (bold, italic, fonts, colors)
✅ Terminology glossary for consistency
✅ BERT-based phrase alignment
✅ Multiple translator backends
✅ Background job processing
✅ Web UI + REST API

---

## 🛠️ Next Steps

- Add Redis for distributed job queue
- Add authentication (API keys)
- Add layout adjustment API
- Add batch processing
- Add webhooks

See `docs/API_GUIDE.md` for details.

---

**Questions?** Check `docs/API_GUIDE.md` or `CLAUDE.md`
