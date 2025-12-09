# Railway Deployment Guide

This guide explains how to deploy the PowerPoint Translation API to Railway.

## Overview

The application has been optimized for Railway deployment with:
- ✅ Automatic file cleanup (24-hour retention)
- ✅ Ephemeral storage (no persistent volumes needed)
- ✅ Environment variable configuration
- ✅ Health checks and auto-restart
- ✅ System dependencies (LibreOffice, Poppler, Playwright)

## Architecture

**Current Hybrid Setup**:
- Railway: Runs the FastAPI server + Ultimate Translation (Gemini Vision)
- RunPod: Handles GPU-intensive regular translation (BERT alignment)

**Why This Works**:
- Ultimate Translation uses Gemini Vision API (no GPU needed locally)
- Regular translation is forwarded to RunPod serverless endpoint
- Railway only needs CPU resources

## File Storage Strategy

Railway uses **ephemeral storage** by default (files persist during container lifetime):

✅ **This is perfect for our use case because**:
- Users download files immediately after processing (within minutes)
- Old files are automatically cleaned up every 24 hours
- No need for persistent volumes or S3 storage
- Simpler deployment and lower costs

**Automatic Cleanup** (added in api.py):
- Runs on server startup
- Runs periodically on each new upload
- Deletes files older than 24 hours
- Configurable via `FILE_RETENTION_HOURS`

## Prerequisites

1. Railway account (https://railway.app)
2. Git repository with your code
3. API keys ready:
   - `GEMINI_API_KEY` (for Ultimate Translation)
   - `RUNPOD_ENDPOINT_ID` (for regular translation)
   - `RUNPOD_API_KEY` (for regular translation)

## Deployment Steps

### 1. Prepare Your Repository

Ensure these files are committed:
- `railway.toml` (Railway configuration)
- `requirements.txt` (Python dependencies)
- `api.py` (FastAPI server)
- All `ultimate_translation/` files
- `.env` (NOT committed - will set via Railway dashboard)

### 2. Create Railway Project

```bash
# Option A: Deploy from GitHub
1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect Python and use railway.toml

# Option B: Deploy via CLI
npm install -g @railway/cli
railway login
railway init
railway up
```

### 3. Configure Environment Variables

In Railway dashboard, add these variables:

```bash
# Required for Ultimate Translation
GEMINI_API_KEY=your_gemini_api_key_here

# Required for RunPod integration
USE_RUNPOD=true
RUNPOD_ENDPOINT_ID=your_endpoint_id
RUNPOD_API_KEY=your_runpod_api_key

# Optional: File cleanup settings
FILE_RETENTION_HOURS=24

# Railway sets these automatically:
# PORT=<assigned_by_railway>
```

### 4. System Dependencies

Railway's Nixpacks builder will automatically install:
- Python 3.11+
- LibreOffice (for PPT → PDF conversion)
- Poppler (for PDF → image conversion)
- Chromium (for Playwright HTML → PDF)

These are specified in `requirements.txt` and will be detected automatically.

### 5. Verify Deployment

After deployment:

1. **Check Health**:
   ```bash
   curl https://your-app.railway.app/health
   ```

2. **Test Upload**:
   ```bash
   curl -X POST https://your-app.railway.app/api/translate/ultimate \
     -F "file=@test.pptx" \
     -F "use_glossary=true"
   ```

3. **Monitor Logs**:
   - Go to Railway dashboard
   - Click your service → Logs
   - Look for startup cleanup messages

## File Cleanup Configuration

The cleanup system is already integrated. To customize:

**Change retention period** (in `api.py`):
```python
FILE_RETENTION_HOURS = 24  # Change to 12, 48, etc.
```

**Manual cleanup endpoint** (optional - add to api.py if needed):
```python
@app.post("/api/admin/cleanup")
async def manual_cleanup():
    """Manually trigger file cleanup."""
    deleted = cleanup_old_files()
    return {"deleted_files": deleted}
```

## Cost Optimization

**Railway Pricing** (as of 2024):
- Free tier: 500 execution hours/month
- Pro tier: $5/month base + usage

**Estimated costs for this app**:
- Small usage: Free tier sufficient
- Medium usage (100 translations/day): ~$10-20/month
- API costs (Gemini + RunPod) likely exceed Railway costs

**Cost-saving tips**:
1. Use free tier until you hit limits
2. Set aggressive file retention (12 hours instead of 24)
3. Monitor Railway dashboard for resource usage

## Troubleshooting

### Files Not Cleaning Up

Check logs for cleanup errors:
```bash
railway logs --follow
```

Look for: `Cleanup complete: deleted X old files`

### Disk Space Issues

If disk fills up (unlikely with 24h retention):
1. Lower `FILE_RETENTION_HOURS` to 12 or 6
2. Add manual cleanup endpoint
3. Trigger cleanup more frequently

### Download Links Expire

- Downloads work as long as container is running
- Railway containers restart occasionally (platform updates, crashes)
- After restart, old files are gone but new uploads work
- This is expected behavior with ephemeral storage

### LibreOffice or Poppler Missing

Railway should auto-install, but if not:

Create `nixpacks.toml`:
```toml
[phases.setup]
aptPkgs = ["libreoffice", "poppler-utils"]

[phases.install]
cmds = ["pip install -r requirements.txt", "playwright install chromium"]
```

## Updating the Deployment

```bash
# Via Git (automatic deployment)
git add .
git commit -m "Update translation API"
git push origin main

# Railway auto-deploys on push to main branch

# Via Railway CLI
railway up
```

## Monitoring

**Key metrics to watch**:
1. Response times (should be <30s for Ultimate Translation)
2. Disk usage (should stay low with cleanup)
3. Memory usage (should be <2GB)
4. Error rates in logs

**Railway Dashboard**:
- Deployment history
- Real-time logs
- Resource usage graphs
- Custom metrics (if configured)

## Alternative: Persistent Storage

If you later need persistent storage:

**Option 1: Railway Volumes** (for >24h retention)
```bash
# Add volume in Railway dashboard
# Mount at: /app/persistent_storage
# Update api.py to use: Path("/app/persistent_storage/outputs")
```

**Option 2: S3 Integration** (for permanent storage)
```python
# Add boto3 to requirements.txt
# Upload files to S3 after generation
# Return presigned URLs for downloads
```

**Current setup doesn't need these** - ephemeral storage is simpler and sufficient.

## Summary

✅ **Railway can handle downloads perfectly** with the current architecture:
- Files persist during container lifetime (hours to days)
- Users download within minutes of processing
- Old files cleaned up automatically every 24 hours
- No need for complex storage solutions
- Simple, cost-effective deployment

**Next steps**:
1. Push code to GitHub
2. Connect Railway to your repo
3. Set environment variables
4. Deploy and test
5. Monitor usage and costs

**Questions?**
- Railway docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
