# ExplainRX - Vercel Dashboard Deployment Guide

## 🎯 Your Mission: Deploy ExplainRX to a Public URL

Follow these steps exactly and you'll have your app live in about 5 minutes!

---

## 📋 What You'll Need

Copy these values now - you'll paste them into Vercel:

### 1. Your OpenAI API Key
```
Your existing key from .env file (starts with sk-proj-...)
```

### 2. NEW Production Secret Key (generated above)
```
2133ab6633db0a8f708750239a89e66184788788e4107082e128d086f48fac76
```

### 3. Optional: DrugBank Credentials
```
Username: delanceyk
Password: 4Tc.8NM@.5fs.zS
```

---

## 🚀 Step-by-Step Deployment

### Step 1: Go to Vercel

1. Open your browser and go to: **https://vercel.com/new**
2. Sign in with GitHub (if not already logged in)

### Step 2: Import Your Repository

1. You'll see a page titled "Import Git Repository"
2. Look for your repository: **`kld29-collab/bigdatahw`**
3. Click the **"Import"** button next to it

> **Don't see it?** Click "Add GitHub Account" or "Adjust GitHub App Permissions"

### Step 3: Configure Project

You'll see a configuration screen. Here's what to do:

#### A. Project Settings
- **Project Name**: `explainrx` (it should auto-fill from vercel.json)
- **Framework Preset**: Should say "Other" - that's correct!
- **Root Directory**: 
  - Click "Edit" 
  - Type: `med-app`
  - This tells Vercel where your Flask app lives

#### B. Build & Development Settings
- Leave these as default (Vercel auto-detects Python/Flask)
- No need to change "Build Command" or "Output Directory"

### Step 4: Add Environment Variables ⚠️ IMPORTANT!

This is the critical step! Click on **"Environment Variables"** to expand the section.

Add these THREE variables:

#### Variable 1: OpenAI API Key
```
Name:  OPENAI_API_KEY
Value: [Paste your OpenAI key from .env - starts with sk-proj-]

☑️ Production
☑️ Preview  
☑️ Development
```

#### Variable 2: Secret Key (NEW ONE!)
```
Name:  SECRET_KEY
Value: 2133ab6633db0a8f708750239a89e66184788788e4107082e128d086f48fac76

☑️ Production
☑️ Preview
☑️ Development
```

#### Variable 3 & 4: DrugBank (Optional but recommended)
```
Name:  DRUGBANK_USERNAME
Value: delanceyk

☑️ Production
☑️ Preview
☑️ Development
```

```
Name:  DRUGBANK_PASSWORD
Value: 4Tc.8NM@.5fs.zS

☑️ Production
☑️ Preview
☑️ Development
```

> **Important**: Make sure ALL THREE checkboxes are checked for each variable!

### Step 5: Deploy! 🎊

1. Click the big blue **"Deploy"** button
2. Watch the build logs (takes 1-3 minutes)
3. You'll see messages like:
   - "Building..."
   - "Installing dependencies..."
   - "Deployment ready"

### Step 6: Success! 🎉

Once deployment completes:

1. You'll see a **"Congratulations"** screen
2. Your app URL will be displayed (something like):
   - `https://explainrx.vercel.app` or
   - `https://explainrx-kld29-collab.vercel.app`
3. Click **"Visit"** to see your live app!

---

## 🧪 Testing Your Deployed App

Visit your new URL and try these queries:

1. **"Can I take aspirin with ibuprofen?"**
2. **"What are the side effects of metformin?"**
3. **"Is it safe to mix vitamin D with my blood pressure medication?"**

If you see responses, **congratulations!** Your app is live! 🎊

---

## 🔧 Troubleshooting

### Problem: Build Failed

**Check the logs:**
1. In the deployment screen, look at the "Building" section
2. Common issues:
   - Missing dependencies → Check `requirements.txt`
   - Python version issues → Vercel uses Python 3.9 by default

**Solution:**
- Click "Redeploy" after fixing issues
- Or go to your project → Settings → Redeploy

### Problem: 500 Internal Server Error

**This usually means missing environment variables!**

1. Go to: Vercel Dashboard → Your Project → Settings → Environment Variables
2. Verify ALL THREE variables are present:
   - `OPENAI_API_KEY`
   - `SECRET_KEY`
   - `DRUGBANK_USERNAME` (optional)
   - `DRUGBANK_PASSWORD` (optional)
3. Click "Redeploy" in the Deployments tab

### Problem: Can't Find My Repository

**Solution:**
1. Click "Add GitHub Account" or "Adjust GitHub App Permissions"
2. Grant Vercel access to your `bigdatahw` repository
3. Go back to https://vercel.com/new

### Problem: Root Directory Not Working

**Solution:**
1. In project settings, try these options:
   - Leave blank (Vercel might detect it automatically)
   - Or set to: `med-app`
   - Or set to: `Med App/med-app` (if nested differently)

### Problem: Static Files Not Loading (CSS/JS)

**Solution:**
- This should work automatically with our `vercel.json` configuration
- If not, check Runtime Logs: Dashboard → Your Project → Deployments → Runtime Logs

---

## 📱 Managing Your Deployment

### View Logs
1. Vercel Dashboard → Your Project
2. Click on latest deployment
3. Click "Runtime Logs" to see errors

### Update Environment Variables
1. Dashboard → Your Project → Settings → Environment Variables
2. Add/Edit/Delete variables
3. **Important**: Click "Redeploy" after changing variables!

### Redeploy
Every time you push to GitHub, Vercel auto-deploys. Or:
1. Dashboard → Your Project → Deployments
2. Click "..." menu on any deployment
3. Click "Redeploy"

### Custom Domain (Later)
1. Dashboard → Your Project → Settings → Domains
2. Add your domain (e.g., `explainrx.com`)
3. Follow DNS setup instructions

---

## ✅ Post-Deployment Checklist

- [ ] App loads at your Vercel URL
- [ ] Can submit a query about medication interactions
- [ ] Gets a response from OpenAI
- [ ] No console errors (check browser DevTools)
- [ ] Environment variables are set
- [ ] Share your URL with friends/testers!

---

## 🎓 Your URLs

After deployment, you'll have:

- **Production**: `https://explainrx.vercel.app` (or similar)
- **GitHub Repo**: `https://github.com/kld29-collab/bigdatahw`
- **Vercel Dashboard**: `https://vercel.com/dashboard`

---

## 🆘 Need More Help?

- Full guide: See `DEPLOYMENT.md`
- Quick reference: See `QUICKSTART_DEPLOY.md`
- Vercel docs: https://vercel.com/docs

---

**Good luck! You've got this! 🚀**
