# RunPod Serverless Deployment Guide

Complete guide to deploying the PowerPoint Translation system on RunPod Serverless.

## Why RunPod Serverless?

- ✅ **Pay-per-second** - Only charged when translating (no idle costs)
- ✅ **Auto-scaling** - Handles 1 or 100 concurrent users automatically
- ✅ **GPU access** - Fast local LLM translation
- ✅ **Fast cold starts** - Optimized Docker image (~15-30 second startup)
- ✅ **Cost-effective** - ~$0.0004/second ($0.024/minute) on RTX 4090

**Estimated costs:**
- Small presentation (10 slides): ~$0.05-0.10
- Medium presentation (30 slides): ~$0.15-0.30
- Large presentation (100 slides): ~$0.50-1.00

---

## Prerequisites

1. **RunPod Account**
   - Sign up at https://runpod.io
   - Add credit (minimum $10 recommended)

2. **Docker Hub Account** (or other registry)
   - Sign up at https://hub.docker.com
   - Create a repository (e.g., `yourusername/pptx-translator`)

3. **Local Tools**
   - Docker installed on your machine
   - Git

---

## Step 1: Build and Push Docker Image

### Option A: Build Locally (Faster for testing)

```bash
cd /Users/jasonhao/Desktop/fast_align_test/translationAPP_2ed

# Build the Docker image
docker build -f Dockerfile.runpod -t yourusername/pptx-translator:latest .

# Login to Docker Hub
docker login

# Push to Docker Hub
docker push yourusername/pptx-translator:latest
```

**Note:** This will take 10-30 minutes depending on your internet speed.

### Option B: Build on RunPod (Better for large images)

Upload your code to GitHub, then use RunPod's builder:

```bash
# 1. Push code to GitHub
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/pptx-translator.git
git push -u origin main

# 2. Use RunPod's Docker Builder (in RunPod console)
# Build from: https://github.com/yourusername/pptx-translator
# Dockerfile: Dockerfile.runpod
```

---

## Step 2: Create RunPod Serverless Endpoint

1. Go to https://www.runpod.io/console/serverless

2. Click **"+ New Endpoint"**

3. Configure the endpoint:
   ```
   Name: pptx-translator

   Select GPU:
   - RTX 4090 (Recommended - $0.00039/sec)
   - RTX 3090 (Budget - $0.00029/sec)
   - A100 (Faster - $0.00089/sec)

   Container Image: yourusername/pptx-translator:latest

   Container Disk: 20 GB (minimum)

   GPU Memory: 24 GB (for RTX 4090/A100)

   Environment Variables:
   - BERT_DEVICE=cuda
   - TRANSLATOR_TYPE=local

   Active Workers:
   - Min: 0 (scale to zero when idle)
   - Max: 3 (adjust based on expected load)

   GPU IDs: Leave empty (auto-select)

   Idle Timeout: 60 seconds

   FlashBoot: Enabled (faster cold starts)
   ```

4. Click **"Deploy"**

5. Wait for endpoint to be ready (status: "Ready")

6. Copy your **Endpoint ID** (looks like: `abc123def456`)

---

## Step 3: Get Your API Key

1. Go to https://www.runpod.io/console/serverless

2. Click on **Settings** → **API Keys**

3. Create a new API key

4. Copy and save it securely (looks like: `ABCDEFGH1234567890`)

---

## Step 4: Test Your Endpoint

### Using curl:

```bash
# Set your credentials
export RUNPOD_ENDPOINT_ID="your-endpoint-id"
export RUNPOD_API_KEY="your-api-key"

# Encode your PowerPoint file to base64
FILE_BASE64=$(base64 -i slides/presentation.pptx)

# Send request
curl -X POST \
  "https://api.runpod.ai/v2/${RUNPOD_ENDPOINT_ID}/runsync" \
  -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"input\": {
      \"file_base64\": \"${FILE_BASE64}\",
      \"file_name\": \"presentation.pptx\",
      \"translator_type\": \"local\",
      \"use_glossary\": true
    }
  }"
```

### Using Python:

```python
import runpod
import base64

# Configure RunPod
runpod.api_key = "your-api-key"
endpoint = runpod.Endpoint("your-endpoint-id")

# Read and encode file
with open("presentation.pptx", "rb") as f:
    file_bytes = f.read()
    file_base64 = base64.b64encode(file_bytes).decode('utf-8')

# Run translation
result = endpoint.run_sync({
    "file_base64": file_base64,
    "file_name": "presentation.pptx",
    "translator_type": "local",
    "use_glossary": True
})

# Decode and save result
if "file_base64" in result:
    output_bytes = base64.b64decode(result["file_base64"])
    with open("translated.pptx", "wb") as f:
        f.write(output_bytes)
    print("Translation complete!")
    print(f"Stats: {result['stats']}")
else:
    print(f"Error: {result.get('error')}")
```

---

## Step 5: Create a Web Frontend (Optional)

You can create a simple web interface that calls RunPod:

```html
<!-- Simple HTML frontend -->
<!DOCTYPE html>
<html>
<body>
    <input type="file" id="fileInput" accept=".pptx">
    <button onclick="translate()">Translate</button>
    <div id="status"></div>

    <script>
    async function translate() {
        const file = document.getElementById('fileInput').files[0];
        const reader = new FileReader();

        reader.onload = async (e) => {
            const base64 = btoa(e.target.result);

            const response = await fetch(
                'https://api.runpod.ai/v2/YOUR-ENDPOINT-ID/runsync',
                {
                    method: 'POST',
                    headers: {
                        'Authorization': 'Bearer YOUR-API-KEY',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        input: {
                            file_base64: base64,
                            file_name: file.name,
                            translator_type: 'local'
                        }
                    })
                }
            );

            const result = await response.json();
            // Handle result...
        };

        reader.readAsBinaryString(file);
    }
    </script>
</body>
</html>
```

---

## Pricing Breakdown

### RunPod Serverless Costs (RTX 4090):

- **Compute:** $0.00039/second = $0.023/minute
- **Storage:** ~$0.10/GB/month (for Docker image)

### Example Translation Costs:

| Presentation Size | Translation Time | Cost |
|-------------------|------------------|------|
| 10 slides | 2 minutes | $0.05 |
| 30 slides | 5 minutes | $0.12 |
| 50 slides | 8 minutes | $0.19 |
| 100 slides | 15 minutes | $0.35 |

### Monthly Costs (Estimated):

- **Light usage** (10 presentations/month): ~$1-2
- **Medium usage** (50 presentations/month): ~$5-10
- **Heavy usage** (200 presentations/month): ~$20-40

**Note:** Costs scale linearly - you only pay for what you use!

---

## Optimization Tips

### 1. Reduce Image Size

```dockerfile
# Use multi-stage builds
FROM python:3.10-slim AS builder
# ... build dependencies ...

FROM python:3.10-slim
COPY --from=builder /app /app
```

### 2. Pre-download Models

Already included in `Dockerfile.runpod`:
- BERT model is pre-downloaded
- LLM model can be pre-downloaded (uncomment in Dockerfile)

### 3. Increase Workers for High Traffic

If you expect concurrent users:
```
Min Workers: 1 (always 1 ready)
Max Workers: 5 (scale up to 5)
```

Trade-off: Faster response vs. higher idle costs

### 4. Use Smaller GPU for Testing

For development/testing:
- Switch to RTX 3090 ($0.00029/sec)
- 20% cheaper, slightly slower

---

## Monitoring and Debugging

### View Logs

1. Go to RunPod Console → Your Endpoint
2. Click **"Logs"** tab
3. View real-time logs from your handler

### Check Metrics

1. Click **"Analytics"** tab
2. View:
   - Total requests
   - Average execution time
   - Error rate
   - Cost breakdown

### Common Issues

**Issue: "Container failed to start"**
- Check Docker image is public or RunPod has access
- Verify Dockerfile.runpod builds successfully locally

**Issue: "Out of memory"**
- Increase Container Disk to 30GB
- Use smaller BERT model
- Switch to larger GPU (A100)

**Issue: "Timeout"**
- Increase timeout in endpoint settings (default: 300s)
- For large presentations, may need 600s+

**Issue: "Slow cold starts"**
- Enable FlashBoot
- Pre-download all models in Dockerfile
- Reduce image size

---

## Security Considerations

1. **API Key Protection**
   - Never commit API keys to GitHub
   - Use environment variables
   - Rotate keys regularly

2. **Input Validation**
   - Handler already validates file format
   - Consider adding file size limits

3. **Output Storage**
   - Results are ephemeral (not stored on RunPod)
   - You're responsible for storing translated files

---

## Scaling to Production

### Option 1: RunPod + Your Own Backend

```
User → Your Server (FastAPI) → RunPod Serverless → Response
```

Benefits:
- File storage on your server
- User authentication
- Job history/tracking
- Multiple RunPod endpoints (failover)

### Option 2: Direct RunPod Access

```
User → RunPod Serverless → Response
```

Benefits:
- Simpler architecture
- Lower latency
- No server costs

### Option 3: Hybrid

```
User → CloudFlare Workers → RunPod → S3 Storage
```

Benefits:
- Global CDN
- Automatic file storage
- Cheap hosting

---

## Next Steps

1. ✅ Build and push Docker image
2. ✅ Create RunPod endpoint
3. ✅ Test with sample file
4. ⏳ Optimize image size (if needed)
5. ⏳ Create production frontend
6. ⏳ Set up monitoring/alerts
7. ⏳ Configure auto-scaling

---

## Support and Resources

- **RunPod Docs:** https://docs.runpod.io/serverless/overview
- **RunPod Discord:** https://discord.gg/runpod
- **Pricing Calculator:** https://www.runpod.io/pricing

---

## Cost Comparison

| Platform | Cost/Month (50 presentations) | Pros | Cons |
|----------|-------------------------------|------|------|
| **RunPod Serverless** | $5-10 | Pay-per-use, auto-scale | Cold starts |
| **RunPod GPU Pod** | $200-400 | Always ready, no cold start | 24/7 costs |
| **OpenAI API** | $10-20 | No infra, fast | Per-token costs |
| **AWS Lambda + Bedrock** | $15-30 | Serverless, reliable | More complex |

**Recommendation:** Start with RunPod Serverless, migrate to GPU Pod only if you need 24/7 availability.

---

Questions? Check the troubleshooting section or reach out on RunPod Discord!
