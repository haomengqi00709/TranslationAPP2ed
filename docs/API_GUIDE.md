# API Guide

Complete guide for running the PowerPoint Translation API.

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Build and run with docker-compose
docker-compose up --build

# API will be available at http://localhost:8000
# Web UI at http://localhost:8000
```

### Option 2: Local Python

```bash
# Activate virtual environment
source myenv/bin/activate

# Install additional dependencies
pip install fastapi uvicorn python-multipart

# Run API server
python api.py

# Or use uvicorn directly
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

---

## API Endpoints

### 1. **POST /api/translate**

Upload and translate a PowerPoint presentation.

**Request:**
```bash
curl -X POST http://localhost:8000/api/translate \
  -F "file=@presentation.pptx" \
  -F "translator_type=local" \
  -F "use_glossary=true" \
  -F "context=Use formal tone"
```

**Parameters:**
- `file` (required): PowerPoint file (.pptx)
- `translator_type` (optional): `local`, `openai`, or `anthropic` (default: `local`)
- `use_glossary` (optional): `true` or `false` (default: `true`)
- `context` (optional): Additional instructions for translation

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Translation job created successfully",
  "status_url": "/api/status/550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 2. **GET /api/status/{job_id}**

Check translation job status.

**Request:**
```bash
curl http://localhost:8000/api/status/550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "message": "Translation completed successfully",
  "created_at": "2025-10-23T10:30:00",
  "updated_at": "2025-10-23T10:35:00",
  "download_url": "/api/download/550e8400-e29b-41d4-a716-446655440000"
}
```

**Status values:**
- `pending`: Job created, waiting to start
- `processing`: Translation in progress
- `completed`: Translation finished, ready to download
- `failed`: Translation failed (see `error` field)

---

### 3. **GET /api/download/{job_id}**

Download translated PowerPoint file.

**Request:**
```bash
curl -O -J http://localhost:8000/api/download/550e8400-e29b-41d4-a716-446655440000
```

**Response:**
- Content-Type: `application/vnd.openxmlformats-officedocument.presentationml.presentation`
- File: `{original_name}_translated.pptx`

---

### 4. **GET /api/glossary**

Get current glossary entries.

**Request:**
```bash
curl http://localhost:8000/api/glossary
```

**Response:**
```json
{
  "entries": [
    {
      "source": "Senate",
      "target": "Sénat",
      "priority": 10,
      "case_sensitive": true,
      "context": null,
      "notes": "Canadian Senate (upper house)"
    }
  ],
  "count": 1
}
```

---

### 5. **DELETE /api/jobs/{job_id}**

Delete a job and its files.

**Request:**
```bash
curl -X DELETE http://localhost:8000/api/jobs/550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "message": "Job deleted successfully"
}
```

---

### 6. **GET /health**

Health check endpoint.

**Request:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "glossary_loaded": true,
  "glossary_entries": 16
}
```

---

## Docker Deployment

### Basic Deployment

```bash
# Build image
docker-compose build

# Run container
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop container
docker-compose down
```

### GPU Support (for Local LLM)

Uncomment the GPU section in `docker-compose.yml`:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

Then run:
```bash
docker-compose up --build
```

**Requirements:**
- NVIDIA GPU
- nvidia-docker installed
- CUDA drivers

### Environment Variables

Create `.env` file:

```bash
# Translation settings
TRANSLATOR_TYPE=local
SOURCE_LANGUAGE=English
TARGET_LANGUAGE=French

# BERT settings
BERT_DEVICE=cpu
BERT_MODEL_NAME=sentence-transformers/LaBSE

# API keys (for cloud translators)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Logging
LOG_LEVEL=INFO
```

---

## Python Client Example

```python
import requests
import time

# Upload file
with open("presentation.pptx", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/translate",
        files={"file": f},
        params={
            "translator_type": "local",
            "use_glossary": True
        }
    )

job_id = response.json()["job_id"]
print(f"Job created: {job_id}")

# Poll status
while True:
    status = requests.get(f"http://localhost:8000/api/status/{job_id}").json()
    print(f"Status: {status['status']} - {status['message']} ({status['progress']}%)")

    if status["status"] == "completed":
        break
    elif status["status"] == "failed":
        print(f"Error: {status['error']}")
        exit(1)

    time.sleep(2)

# Download result
response = requests.get(f"http://localhost:8000/api/download/{job_id}")
with open("translated.pptx", "wb") as f:
    f.write(response.content)

print("Translation complete!")
```

---

## Testing with Web UI

1. Start the API:
   ```bash
   docker-compose up
   ```

2. Open browser:
   ```
   http://localhost:8000
   ```

3. Upload a PowerPoint file

4. Select translation options

5. Click "Start Translation"

6. Download translated file when complete

---

## Production Deployment

### Cloud Deployment Options

#### 1. **Local Machine + ngrok (Development)**

```bash
# Run API locally
docker-compose up

# In another terminal, expose via ngrok
ngrok http 8000
```

Your API will be accessible at: `https://xxxx-xx-xx-xxx-xx.ngrok-free.app`

**Pros:**
- Free
- Easy setup
- Good for testing

**Cons:**
- Requires your machine to be on
- Limited to your GPU capacity

---

#### 2. **Cloud GPU (RunPod, Vast.ai, Lambda Labs)**

```bash
# SSH into GPU instance
ssh user@gpu-instance

# Clone repo
git clone <your-repo>
cd translationAPP_2ed

# Run with docker-compose
docker-compose up -d

# Expose port or use reverse proxy
```

**Pros:**
- Pay per hour
- Powerful GPUs
- Good for on-demand usage

**Cons:**
- Costs ~$0.30-$1.00/hour when running

---

#### 3. **Hybrid: Cloud API + Local GPU**

Use OpenAI/Anthropic API for translation, run BERT alignment locally:

```bash
# Set environment
export TRANSLATOR_TYPE=openai
export OPENAI_API_KEY=sk-...

# Run API (CPU only, no GPU needed)
docker-compose up
```

**Pros:**
- No GPU required
- Fast translation
- Always available

**Cons:**
- API costs (~$0.01-0.05 per slide)

---

## Monitoring and Logs

```bash
# View live logs
docker-compose logs -f

# View specific service
docker-compose logs -f api

# Check container status
docker-compose ps

# Check resource usage
docker stats
```

---

## Troubleshooting

### API won't start

```bash
# Check logs
docker-compose logs api

# Common issues:
# - Port 8000 already in use: Change port in docker-compose.yml
# - Missing dependencies: Rebuild with docker-compose build --no-cache
```

### Translation fails

```bash
# Check job status
curl http://localhost:8000/api/status/{job_id}

# Common issues:
# - Out of memory: Reduce BERT_MAX_PHRASE_LENGTH in config.py
# - GPU not available: Set BERT_DEVICE=cpu
# - API key invalid: Check OPENAI_API_KEY or ANTHROPIC_API_KEY
```

### Slow translation

- **Local LLM**: Ensure GPU is enabled
- **Cloud API**: Check network connection
- **BERT alignment**: Reduce max_phrase_length or use smaller model

---

## API Rate Limits

Current implementation has **no rate limiting**. For production, add rate limiting:

```python
# In api.py, add:
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/translate")
@limiter.limit("5/minute")  # 5 requests per minute
async def translate(...):
    ...
```

---

## Security Considerations

1. **File Upload Size**: Limited by FastAPI default (16MB)
   - Increase with: `app = FastAPI(max_request_size=50*1024*1024)`  # 50MB

2. **File Validation**: Only `.pptx` files accepted
   - Additional validation: Check file signature

3. **API Keys**: Store in environment variables, not code
   - Use `.env` file or secrets manager

4. **HTTPS**: Use reverse proxy (nginx, Caddy) for SSL
   - Or deploy behind cloud load balancer

---

## Next Steps

1. **Add Redis job queue** (for multiple workers)
2. **Add authentication** (API keys, OAuth)
3. **Add webhooks** (notify when job completes)
4. **Add batch processing** (multiple files at once)
5. **Add layout adjustment API** (separate endpoint)

See `CLAUDE.md` for roadmap and future features.
