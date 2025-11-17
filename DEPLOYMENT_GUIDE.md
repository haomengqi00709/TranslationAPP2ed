# Deployment Guide: Vercel + Railway

This guide shows you how to deploy your PowerPoint translation app as a real public website.

## Architecture

```
User Browser
    ↓
Vercel (Frontend - HTML/CSS/JS)
    ↓ API calls
Railway (Backend - FastAPI)
    ↓ Forward translation
RunPod Serverless (GPU Translation)
```

---

## Prerequisites

1. **GitHub Account** (to store code)
2. **Vercel Account** (sign up at https://vercel.com - free)
3. **Railway Account** (sign up at https://railway.app - free)

---

## Part 1: Prepare Your Code

### 1. Create a GitHub Repository

```bash
cd /Users/jasonhao/Desktop/fast_align_test/translationAPP_2ed

# Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit - PowerPoint translation app"

# Create a new repo on GitHub, then:
git remote add origin https://github.com/YOUR-USERNAME/pptx-translator.git
git branch -M main
git push -u origin main
```

### 2. Add Required Files

We need to create a few files for deployment:

- `requirements.txt` (Python dependencies)
- `railway.json` (Railway configuration)
- `vercel.json` (Vercel configuration)
- `.env.example` (Environment variables template)

These are already created in your project!

---

## Part 2: Deploy Backend to Railway

### Step 1: Sign Up for Railway

1. Go to https://railway.app
2. Click "Start a New Project"
3. Sign in with GitHub

### Step 2: Deploy from GitHub

1. Click "Deploy from GitHub repo"
2. Select your `pptx-translator` repository
3. Railway will detect it's a Python app

### Step 3: Configure Environment Variables

In Railway dashboard, add these environment variables:

```
USE_RUNPOD=true
RUNPOD_ENDPOINT_ID=io6lj6wjt80mqe
RUNPOD_API_KEY=rpa_3O2QGMN26HIIKM3L345AXOB3MH3XWX0N14KZX9TJ13ggys
PORT=8000
```

### Step 4: Set Start Command

In Railway settings, set the start command:

```
uvicorn api:app --host 0.0.0.0 --port $PORT
```

### Step 5: Get Your Backend URL

Railway will give you a URL like:
```
https://pptx-translator-production.up.railway.app
```

**Save this URL!** You'll need it for the frontend.

---

## Part 3: Deploy Frontend to Vercel

### Option A: Deploy via Vercel Dashboard (Easiest)

1. Go to https://vercel.com/new
2. Click "Add New" → "Project"
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Other
   - **Root Directory**: `frontend`
   - **Build Command**: (leave empty - it's static HTML)
   - **Output Directory**: `.` (current directory)

5. Add Environment Variable:
   ```
   VITE_API_URL=https://your-railway-url.up.railway.app
   ```

6. Click "Deploy"

### Option B: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd frontend
vercel --prod
```

When prompted:
- Project name: `pptx-translator`
- Set up and deploy: `Yes`

---

## Part 4: Update Frontend to Use Railway Backend

Edit `frontend/index.html` and update the API URL:

Find these lines:
```javascript
const response = await fetch(`/api/translate?...
```

Change to:
```javascript
const API_URL = 'https://your-railway-url.up.railway.app';
const response = await fetch(`${API_URL}/api/translate?...
```

**Or better:** Create a config at the top of the script:

```javascript
// Configuration
const API_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'  // Local development
    : 'https://your-railway-url.up.railway.app';  // Production
```

Then use `${API_URL}/api/translate` everywhere.

---

## Part 5: Test Your Deployment

1. Visit your Vercel URL: `https://pptx-translator.vercel.app`
2. Upload a PowerPoint file
3. Click "Translate"
4. Wait for completion (4-5 minutes)
5. Download the result

---

## Costs Breakdown

| Service | Free Tier | Paid (if exceeded) |
|---------|-----------|-------------------|
| **Vercel** | 100 GB bandwidth/month | $20/month Pro plan |
| **Railway** | $5 credit/month (~500 hours) | $0.01/hour after credit |
| **RunPod** | Pay-per-use only | ~$0.30-0.50 per translation |

**Typical monthly cost for 100 translations:**
- Vercel: **$0** (well within free tier)
- Railway: **$0** (well within free tier)
- RunPod: **$30-50** (100 translations × $0.30-0.50)

**Total: ~$30-50/month** (only when people actually use it!)

---

## Custom Domain (Optional)

Want `translate.yourdomain.com` instead of Vercel subdomain?

### On Vercel:
1. Go to your project → Settings → Domains
2. Add your custom domain
3. Follow DNS instructions

### On Railway:
1. Go to your service → Settings → Networking
2. Add custom domain
3. Update DNS with provided CNAME

---

## Troubleshooting

### CORS Errors

If you get CORS errors, make sure `api.py` has:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your Vercel domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Railway Service Won't Start

Check logs in Railway dashboard. Common issues:
- Missing environment variables
- Wrong start command
- Missing dependencies in `requirements.txt`

### Frontend Can't Reach Backend

- Check that Railway URL is correct in frontend code
- Check that Railway service is running (green status)
- Check browser console for error messages

---

## Alternative: All-in-One on Render

If you prefer a simpler setup, you can deploy everything to Render:

1. Go to https://render.com
2. Create a "Web Service" for the backend
3. Create a "Static Site" for the frontend
4. Connect your GitHub repo
5. Set environment variables

Render's free tier:
- Static sites: Unlimited
- Web services: 750 hours/month (spins down after 15min idle)

---

## Next Steps

After deployment:
1. Share the Vercel URL with others
2. Monitor usage in Railway/RunPod dashboards
3. Consider adding user authentication (if needed)
4. Set up error monitoring (Sentry)
5. Add analytics (Google Analytics, Plausible)

---

## Security Notes

**Important:**
- Your RunPod API key is stored on Railway (server-side) ✅
- It's NOT exposed to the browser ✅
- HTTPS is automatic on both Vercel and Railway ✅

For production, consider:
- Rate limiting (to prevent abuse)
- User authentication (if you want to restrict access)
- File size limits (already in place)
- Monitoring and alerts

---

## Support

If you encounter issues:
- Railway: Check logs in dashboard
- Vercel: Check deployment logs
- RunPod: Check serverless logs

Feel free to ask for help!
