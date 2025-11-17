# Deployment Checklist for Railway + Vercel

Follow these steps to deploy your PowerPoint translator to the web!

## ✅ Prerequisites (5 minutes)

- [ ] GitHub account created
- [ ] Railway account created (https://railway.app - sign up with GitHub)
- [ ] Vercel account created (https://vercel.com - sign up with GitHub)

---

## 📦 Step 1: Push Code to GitHub (10 minutes)

```bash
cd /Users/jasonhao/Desktop/fast_align_test/translationAPP_2ed

# Initialize git repository
git init

# Add all files
git add .

# Create first commit
git commit -m "Initial commit - PowerPoint translation app with RunPod backend"

# Create a new repository on GitHub (go to github.com/new)
# Name it: pptx-translator
# Then run:
git remote add origin https://github.com/YOUR-USERNAME/pptx-translator.git
git branch -M main
git push -u origin main
```

**✅ Verify:** Your code should now be visible on GitHub!

---

## 🚂 Step 2: Deploy Backend to Railway (10 minutes)

### 2.1 Create New Project

1. Go to https://railway.app/new
2. Click **"Deploy from GitHub repo"**
3. Select your **`pptx-translator`** repository
4. Click **"Deploy Now"**

### 2.2 Add Environment Variables

In the Railway dashboard:

1. Click on your deployed service
2. Go to **"Variables"** tab
3. Click **"+ New Variable"** and add these:

```
USE_RUNPOD=true
RUNPOD_ENDPOINT_ID=io6lj6wjt80mqe
RUNPOD_API_KEY=rpa_3O2QGMN26HIIKM3L345AXOB3MH3XWX0N14KZX9TJ13ggys
```

4. Click **"Deploy"** to restart with new variables

### 2.3 Get Your Railway URL

1. Go to **"Settings"** tab
2. Scroll to **"Domains"**
3. Click **"Generate Domain"**
4. **Copy this URL** (e.g., `https://pptx-translator-production.up.railway.app`)

**✅ Verify:** Visit `https://your-railway-url.railway.app/health` - you should see:
```json
{"status": "healthy", "glossary_loaded": true, "glossary_entries": 16}
```

---

## ⚡ Step 3: Deploy Frontend to Vercel (5 minutes)

### 3.1 Update Frontend with Railway URL

**IMPORTANT:** Before deploying to Vercel, update your Railway URL in the frontend:

```bash
# Edit frontend/index.html
# Find line ~405:
# Change this:
: 'https://YOUR_RAILWAY_URL_HERE.railway.app';

# To your actual Railway URL:
: 'https://pptx-translator-production.up.railway.app';
```

Then commit and push:
```bash
git add frontend/index.html
git commit -m "Update Railway URL for production"
git push
```

### 3.2 Deploy to Vercel

1. Go to https://vercel.com/new
2. Click **"Import Project"**
3. Select your **`pptx-translator`** repository
4. Configure settings:
   - **Framework Preset:** Other
   - **Root Directory:** Leave as `.` (it will use the vercel.json config)
   - **Build Command:** Leave empty
   - **Output Directory:** Leave empty
5. Click **"Deploy"**

### 3.3 Get Your Vercel URL

Vercel will give you a URL like:
```
https://pptx-translator.vercel.app
```

**✅ Verify:** Visit your Vercel URL - you should see the PowerPoint translation interface!

---

## 🧪 Step 4: Test End-to-End (5 minutes)

1. **Open your Vercel URL** in a browser
2. **Upload a test PowerPoint** (e.g., `slides/PPT-3-Government-in-Canada1 (2).pptx`)
3. **Click "Translate PowerPoint"**
4. **Wait 4-5 minutes** - you should see progress updates
5. **Download the result** - verify it's translated correctly

**Expected flow:**
```
Browser (Vercel) → Railway API → RunPod Serverless → Railway → Browser
```

---

## 🎉 Step 5: Share Your App!

Your app is now live at: `https://pptx-translator.vercel.app`

Share it with anyone - they can translate PowerPoints for **~$0.30-0.50 per file**!

---

## 💰 Cost Monitoring

### Free Tiers:
- **Vercel:** 100GB bandwidth/month (FREE)
- **Railway:** $5 credit/month (~500 hours) (FREE)
- **RunPod:** Pay per translation (~$0.30-0.50 each)

### Where to Monitor:
- **Railway:** https://railway.app/dashboard (check usage)
- **Vercel:** https://vercel.com/dashboard (check bandwidth)
- **RunPod:** https://www.runpod.io/console/serverless (check GPU usage)

---

## 🔧 Troubleshooting

### Frontend can't reach backend

**Symptom:** CORS errors or "Failed to fetch" in browser console

**Solution:**
1. Check that Railway URL in `frontend/index.html` is correct
2. Verify Railway service is running (green status)
3. Test Railway directly: `https://your-railway-url.railway.app/health`

### Railway deployment failed

**Symptom:** Red status, deployment error

**Solution:**
1. Check Railway logs (click on service → "Deployments" → latest deployment → "View Logs")
2. Common issues:
   - Missing environment variables
   - Python dependencies issue (check `requirements.txt`)
   - Port configuration (Railway automatically sets $PORT)

### Vercel shows 404

**Symptom:** "404 - Page Not Found" on Vercel

**Solution:**
1. Check `vercel.json` is in the root directory
2. Verify `frontend/index.html` exists
3. Redeploy from Vercel dashboard

### Translation times out

**Symptom:** "Request failed" after a long wait

**Solution:**
1. Check RunPod endpoint is active (https://www.runpod.io/console/serverless)
2. Check Railway logs for errors
3. Verify RunPod API key and endpoint ID are correct in Railway environment variables

---

## 🔄 Making Updates

When you want to update your app:

```bash
# Make your changes
# ...

# Commit and push
git add .
git commit -m "Describe your changes"
git push

# Railway and Vercel will automatically redeploy!
```

**Auto-deployment is enabled by default on both platforms!**

---

## 📊 Optional: Add Custom Domain

### For Vercel (Frontend):
1. Go to your project → Settings → Domains
2. Add your domain (e.g., `translate.yoursite.com`)
3. Update your DNS with Vercel's CNAME record

### For Railway (Backend):
1. Go to your service → Settings → Networking
2. Click "Add Custom Domain"
3. Enter your domain (e.g., `api.yoursite.com`)
4. Update your DNS with Railway's CNAME record
5. **Don't forget to update the frontend with the new Railway domain!**

---

## ✅ Final Checklist

- [ ] Code pushed to GitHub
- [ ] Backend deployed to Railway
- [ ] Environment variables added to Railway
- [ ] Railway URL copied
- [ ] Frontend updated with Railway URL
- [ ] Frontend deployed to Vercel
- [ ] End-to-end test successful
- [ ] Shared URL with others

**Congratulations! Your PowerPoint translator is now live! 🎉**

---

## 📚 Additional Resources

- [Railway Docs](https://docs.railway.app)
- [Vercel Docs](https://vercel.com/docs)
- [RunPod Serverless Docs](https://docs.runpod.io/serverless/overview)
- Full deployment guide: `DEPLOYMENT_GUIDE.md`
