# Security Best Practices

## ✅ What Was Fixed

### 1. **Removed Hardcoded API Keys**
- ❌ Before: Keys hardcoded in `config.py` and `scripts/start_api_runpod.sh`
- ✅ Now: Keys stored in `.env` file (git-ignored)

### 2. **Updated Configuration**
- `config.py` - Now reads from environment variables only
- `scripts/start_api_runpod.sh` - Now loads from `.env` file
- `.env.example` - Template for other developers

### 3. **Git Protection**
- `.env` is in `.gitignore` (never committed)
- Hardcoded keys removed from code
- Clean version pushed to GitHub

---

## 🔐 Current Setup

### Local Development

**`.env` file (NOT in Git):**
```bash
# Your actual API keys
OPENAI_API_KEY=sk-proj-...
RUNPOD_API_KEY=rpa_...
RUNPOD_ENDPOINT_ID=io6lj6wjt80mqe
USE_RUNPOD=true
```

**`.env.example` (IN Git):**
```bash
# Template for other developers
OPENAI_API_KEY=your-openai-api-key-here
RUNPOD_API_KEY=your-runpod-api-key-here
...
```

### How It Works Now

1. **You:** Have `.env` with real keys (git-ignored)
2. **Git:** Only has `.env.example` with placeholders
3. **Other developers:** Copy `.env.example` to `.env` and add their own keys

---

## ⚠️ IMPORTANT: Rotate Your API Keys

**Your keys were in Git history briefly. Here's what to do:**

### 1. OpenAI API Key

**Recommended:** Rotate your key (create new one, delete old)

1. Go to: https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the new key
4. Delete the old key (the one starting with `sk-proj-ziU5jDNA...`)
5. Update your `.env` file with the new key

### 2. RunPod API Key

**Recommended:** Rotate your key

1. Go to: https://www.runpod.io/console/user/settings
2. API Keys section
3. Create new API key
4. Delete the old one (the one starting with `rpa_3O2QGMN...`)
5. Update your `.env` file with the new key

### 3. Why Rotate?

Even though your repo is **private**, it's best practice to rotate keys that were exposed in Git history. Better safe than sorry!

---

## 📋 Security Checklist

- [x] API keys moved to `.env` file
- [x] `.env` added to `.gitignore`
- [x] Hardcoded keys removed from code
- [x] `.env.example` created for other developers
- [x] Clean code pushed to GitHub
- [ ] **TODO:** Rotate OpenAI API key
- [ ] **TODO:** Rotate RunPod API key

---

## 🚀 Deployment Security

### Railway Deployment

When deploying to Railway, set environment variables in the Railway dashboard:

1. Go to your Railway project
2. Click "Variables" tab
3. Add:
   ```
   USE_RUNPOD=true
   RUNPOD_ENDPOINT_ID=io6lj6wjt80mqe
   RUNPOD_API_KEY=rpa_... (your NEW key after rotation)
   OPENAI_API_KEY=sk-... (your NEW key after rotation)
   ```

**NEVER** commit these to Git!

### Vercel Deployment

Vercel doesn't need API keys (it's just static HTML).

---

## 🛡️ Future Best Practices

### For This Project

1. **Always use `.env` for secrets**
   ```python
   # Good ✅
   API_KEY = os.getenv("API_KEY")

   # Bad ❌
   API_KEY = "hardcoded-key-here"
   ```

2. **Never commit `.env`**
   - Already in `.gitignore` ✅
   - Check before every commit

3. **Use `.env.example` for templates**
   - Commit this to Git ✅
   - Shows what variables are needed

### For New Developers

When someone clones your repo:

```bash
# 1. Clone repo
git clone https://github.com/haomengqi00709/TranslationAPP2ed.git

# 2. Copy template
cp .env.example .env

# 3. Edit .env with their own keys
nano .env  # or use any text editor

# 4. Run the app
./start_api_runpod.sh
```

---

## 🔍 How to Check for Exposed Secrets

Before committing:

```bash
# Check what's being committed
git diff --cached

# Search for potential secrets
git diff --cached | grep -i "api_key\|secret\|password"
```

If you see actual keys (not just variable names), **DON'T COMMIT!**

---

## 📞 What to Do If Keys Are Exposed

1. **Rotate immediately** (create new, delete old)
2. **Check usage** (look for unauthorized API calls)
3. **Update `.env`** with new keys
4. **Commit the fix** (but keys stay in `.env`, not code)

---

**Last Updated:** 2025-11-17
**Status:** ✅ Secured
