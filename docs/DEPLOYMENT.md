# Deployment Guide

## Quick Start (Recommended)

### Option 1: Deploy via Vercel Web Dashboard (Easiest)

1. **Go to**: https://vercel.com/new
2. **Import Git Repository**: Select your `kld29-collab/med-app` repo
3. **Configure Project**:
   - Project Name: `explainrx`
   - Root Directory: `med-app`
   - Framework: Other (auto-detects Python/Flask)
4. **Add Environment Variables**:
   - `OPENAI_API_KEY`: Your OpenAI API key (starts with sk-proj-...)
   - `SECRET_KEY`: Generate with: `python3 -c "import secrets; print(secrets.token_hex(32))"`
   - `DRUGBANK_USERNAME`: Your DrugBank account username (optional)
   - `DRUGBANK_PASSWORD`: Your DrugBank account password (optional)
5. **Deploy** 🚀 - Takes 1-3 minutes

**Your live URL**: `https://explainrx.vercel.app`

---

### Option 2: Deploy via Vercel CLI (For Updates)

```bash
# Install Vercel CLI (one time only)
npm install -g vercel

# Login to Vercel
vercel login

# Navigate to your project
cd "/Users/kristendelancey/my-repo/Med App/med-app"

# Deploy to production
vercel --prod
```

---

## Complete Deployment Guide

### Prerequisites

- **Vercel Account**: Sign up at [vercel.com](https://vercel.com) (free tier sufficient)
- **Git Repository**: Code must be in a Git repository
- **Environment Variables**: See section below

### Step 1: Prepare Environment Variables

Vercel doesn't use your local `.env` file. Set these in Vercel's dashboard:

#### Required:
- `OPENAI_API_KEY` - Your OpenAI API key
- `SECRET_KEY` - A new secure key for production (generate one!)

#### Optional:
- `DRUGBANK_USERNAME` - For DrugBank integration
- `DRUGBANK_PASSWORD` - For DrugBank integration
- `SERPAPI_API_KEY` - For web search functionality
- `FDA_API_BASE_URL` - Default: `https://api.fda.gov`

**Generate a production SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Step 2: Deploy via Vercel Dashboard

1. **Connect Repository**:
   - Go to [vercel.com/dashboard](https://vercel.com/dashboard)
   - Click "Add New..." → "Project"
   - Import your Git repository
   - Authorize Vercel to access your repo if prompted

2. **Configure Project**:
   - **Project Name**: `explainrx` (from vercel.json)
   - **Framework Preset**: Other (Vercel auto-detects Python)
   - **Root Directory**: `med-app`
   - **Build & Development**: Leave as default

3. **Add Environment Variables**:
   - Click "Environment Variables" section
   - Add each variable with checkboxes: ✓ Production ✓ Preview ✓ Development
   - **Critical**: Make sure all checkboxes are checked

4. **Deploy**:
   - Click "Deploy"
   - Wait for build completion (1-3 minutes)
   - Once done, click "Visit" to see your app

### Step 3: Verify Deployment

Test your app with these queries:
- "Can I take aspirin with ibuprofen?"
- "What are the side effects of metformin?"
- "Is there any food I should avoid with warfarin?"

### Step 4: Continuous Deployment (Auto)

Once connected to Git:
- Push to `main` → **Auto-deploys to production**
- Push to other branches → **Creates preview deployments**
- Pull requests → **Automatic preview URLs**

---

## Troubleshooting

### Build Failures

**Error: Module not found**
- Check all Python files are committed to Git
- Verify `.vercelignore` isn't excluding necessary files
- Run locally: `pip install -r requirements.txt`

**Error: Missing dependencies**
- Verify all packages in `requirements.txt` are spelled correctly
- Check Python version (Vercel uses 3.9+ by default)

### Runtime Errors

**Error: 500 Internal Server Error**
1. Go to: Vercel Dashboard → Your Project → Deployments
2. Click latest deployment → "Runtime Logs"
3. Common causes:
   - Missing environment variables
   - OpenAI API key incorrect
   - DrugBank database initialization failed

**Error: OpenAI API key not found**
- Add `OPENAI_API_KEY` in Vercel environment variables
- **Redeploy** after adding variables

**Error: Database initialization timeout**
- First initialization of DrugBank database can take several minutes
- Vercel has 10-second timeout for serverless functions
- **Solution**: Initialize database locally, commit `data/drugbank.db` to Git
  ```bash
  # Run locally first
  python scripts/init_drugbank_db.py
  
  # Then commit and push
  git add data/drugbank.db
  git commit -m "Add initialized DrugBank database"
  git push
  ```

### View Logs

```bash
# Via CLI
vercel logs explainrx --follow

# Or in Dashboard
Dashboard → Your Project → Deployments → [Click deployment] → Runtime Logs
```

---

## Local Deployment (Development)

### Run Locally

```bash
# Navigate to project
cd "/Users/kristendelancey/my-repo/Med App/med-app"

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your keys
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY and other secrets

# Initialize DrugBank database (one time)
python scripts/init_drugbank_db.py

# Run Flask app
python app.py
```

Your app will be available at: `http://localhost:5000`

---

## Production Checklist

Before going live:

- [ ] New `SECRET_KEY` generated (different from development)
- [ ] `OPENAI_API_KEY` added to Vercel environment variables
- [ ] `.env` file is in `.gitignore` (never commit secrets!)
- [ ] DrugBank database initialized locally (or initialization script will run on first request)
- [ ] Test all major features on deployed URL
- [ ] Set up error monitoring (optional: Sentry, LogRocket)
- [ ] Enable Vercel Analytics (optional, in project settings)
- [ ] Configure rate limiting for API endpoints (recommended)

---

## Useful Commands

```bash
# Deploy to production
vercel --prod

# List deployments
vercel ls

# View logs
vercel logs explainrx

# Remove a project
vercel remove explainrx

# View environment variables
vercel env ls

# Add environment variable
vercel env add VARIABLE_NAME production
```

---

## Performance Notes

- **DrugBank Queries**: ~50ms (local SQLite)
- **RxNorm API**: ~500ms
- **FDA API**: ~500ms
- **Web Search**: ~2000ms
- **LLM (OpenAI)**: ~500-2000ms
- **Total response time**: ~2-5 seconds

---

## Support & Resources

- [Vercel Python Documentation](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
- [Vercel CLI Documentation](https://vercel.com/docs/cli)
- [Flask on Vercel Guide](https://vercel.com/guides/using-flask-with-vercel)

---

## Your URLs

After deployment:

- **Production**: `https://explainrx.vercel.app` (or your custom domain)
- **Preview**: `https://explainrx-[branch-name].vercel.app`
- **Development**: `http://localhost:5000`

---

**Need help?** Check Vercel dashboard logs or run `vercel logs explainrx` for detailed error messages.
