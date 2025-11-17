# Connecting Frontend to Backend

Your frontend (HTML UI) is now connected to the backend via FastAPI. The backend can use either:
- **RunPod Serverless** - GPU in the cloud (pay per use)
- **Local Pipeline** - Run on your machine

## Quick Start

### Option 1: Use RunPod Backend (Recommended)

```bash
./start_api_runpod.sh
```

Then open in your browser:
- **Frontend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Option 2: Use Local Backend

```bash
./start_api_local.sh
```

Same URLs as above.

## How It Works

```
User Browser (Frontend)
    ↓ Upload .pptx
FastAPI Server (api.py)
    ↓ Forward request
RunPod Serverless (GPU)
    ↓ Translate
FastAPI Server
    ↓ Download .pptx
User Browser
```

The FastAPI server acts as a **proxy** between your frontend and RunPod, so:
- ✅ RunPod API key stays secret (not exposed to browser)
- ✅ Can add authentication/rate limiting later
- ✅ Can switch between RunPod/Local without changing frontend
- ✅ Can deploy frontend and API separately

## Configuration

Edit `start_api_runpod.sh` to use your own RunPod credentials:

```bash
export RUNPOD_ENDPOINT_ID="your-endpoint-id"
export RUNPOD_API_KEY="your-api-key"
```

Or create a `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
# Edit .env with your values
```

Then load it before starting:

```bash
source .env
python3 api.py
```

## Testing the API

### Via Frontend (Easy)

1. Start the server: `./start_api_runpod.sh`
2. Open browser: http://localhost:8000
3. Upload a PowerPoint file
4. Click "Translate"
5. Download the result

### Via cURL (Advanced)

```bash
# Upload and start translation
curl -X POST http://localhost:8000/api/translate \
  -F "file=@input.pptx" \
  -F "translator_type=local" \
  -F "use_glossary=true"

# Returns: {"job_id": "abc-123", "status": "pending", ...}

# Check status
curl http://localhost:8000/api/status/abc-123

# Download when completed
curl http://localhost:8000/api/download/abc-123 -o output.pptx
```

### Via Python

```python
import requests

# Upload file
with open("input.pptx", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/translate",
        files={"file": f},
        data={"translator_type": "local", "use_glossary": "true"}
    )
    job_id = response.json()["job_id"]

# Poll for completion
import time
while True:
    status = requests.get(f"http://localhost:8000/api/status/{job_id}").json()
    if status["status"] == "completed":
        break
    print(f"Progress: {status['progress']}%")
    time.sleep(5)

# Download result
result = requests.get(f"http://localhost:8000/api/download/{job_id}")
with open("output.pptx", "wb") as f:
    f.write(result.content)
```

## Deploying to Production

To make this publicly accessible, deploy the FastAPI server to:

1. **Vercel/Netlify** (Frontend only) + **Railway/Fly.io** (API)
2. **Heroku** (Full stack)
3. **AWS EC2/Lambda** (Custom)
4. **Docker + Cloud Run** (Google Cloud)

See `docs/PRODUCTION_DEPLOYMENT.md` for detailed guides (TODO).

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve frontend HTML |
| `/api/translate` | POST | Upload and translate PowerPoint |
| `/api/status/{job_id}` | GET | Check translation status |
| `/api/download/{job_id}` | GET | Download translated file |
| `/api/glossary` | GET | Get current glossary entries |
| `/health` | GET | Health check |

## Troubleshooting

### Port already in use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### RunPod credentials not set
```
WARNING - USE_RUNPOD=true but RUNPOD_ENDPOINT_ID or RUNPOD_API_KEY not set!
WARNING - Falling back to local execution
```

→ Edit `start_api_runpod.sh` with correct credentials

### CORS errors in browser
The API already has CORS enabled (`allow_origins=["*"]`). If you still get errors, check that you're accessing from `http://localhost:8000`, not `file:///`.

### Translation takes too long
RunPod translations typically take 4-5 minutes. The frontend polls for status every 5 seconds and shows progress updates. Check the browser console for detailed logs.
