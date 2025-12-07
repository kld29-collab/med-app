# ExplainRX - Vercel Deployment Guide

This guide will help you deploy your ExplainRX medication interaction tracker to Vercel with a public URL.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com) (free tier is sufficient)
2. **Vercel CLI** (optional but recommended): `npm install -g vercel`
3. **Git**: Your code should be in a Git repository

## Step 1: Prepare Your Environment Variables

Vercel doesn't use your local `.env` file. You need to set environment variables in Vercel's dashboard.

### Required Environment Variables:
- `OPENAI_API_KEY` - Your OpenAI API key
- `SECRET_KEY` - Your Flask secret key (generate a new one for production!)

### Optional Environment Variables:
- `DRUGBANK_USERNAME` - If you want DrugBank integration
- `DRUGBANK_PASSWORD` - If you want DrugBank integration
- `FDA_API_BASE_URL` - Default is `https://api.fda.gov`

## Step 2: Deploy via Vercel Dashboard (Easiest Method)

### A. Connect Your Repository

1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click **"Add New..."** → **"Project"**
3. Import your Git repository:
   - If using GitHub: Click "Import" next to your `bigdatahw` repository
   - Authorize Vercel to access your repository if prompted

### B. Configure Project Settings

1. **Project Name**: `explainrx` (already configured in `vercel.json`)
2. **Framework Preset**: Other (Vercel will auto-detect Python/Flask)
3. **Root Directory**: `med-app` (if your code is in a subdirectory)
4. **Build & Development Settings**: Leave as default

### C. Add Environment Variables

In the project configuration screen:

1. Click **"Environment Variables"**
2. Add each variable:
   ```
   Name: OPENAI_API_KEY
   Value: [your OpenAI API key]
   Environment: Production, Preview, Development (check all)
   ```
3. Add `SECRET_KEY`:
   ```
   Name: SECRET_KEY
   Value: [generate new secure key - see below]
   Environment: Production, Preview, Development (check all)
   ```
4. Add any optional variables (DrugBank credentials, etc.)

**Generate a new production SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### D. Deploy

1. Click **"Deploy"**
2. Wait for the build to complete (1-3 minutes)
3. Once deployed, you'll get a URL like: `https://explainrx.vercel.app`

## Step 3: Deploy via Vercel CLI (Alternative Method)

### A. Install Vercel CLI

```bash
npm install -g vercel
```

### B. Login to Vercel

```bash
vercel login
```

### C. Deploy from Your Project Directory

```bash
cd "/Users/kristendelancey/my-repo/Med App/med-app"
vercel
```

Follow the prompts:
- **Set up and deploy?** Yes
- **Which scope?** Your account
- **Link to existing project?** No
- **Project name?** explainrx
- **Directory?** ./
- **Override settings?** No

### D. Add Environment Variables via CLI

```bash
# Add OpenAI API Key
vercel env add OPENAI_API_KEY production

# Add Secret Key
vercel env add SECRET_KEY production

# Repeat for other environments (preview, development) if needed
```

### E. Redeploy with Environment Variables

```bash
vercel --prod
```

## Step 4: Verify Deployment

1. Visit your Vercel URL (e.g., `https://explainrx.vercel.app`)
2. Test the application:
   - Try a sample query: "Can I take aspirin with ibuprofen?"
   - Check that the interface loads properly
   - Verify API calls are working

## Step 5: Custom Domain (Optional)

1. In Vercel Dashboard → Your Project → Settings → Domains
2. Add your custom domain
3. Follow DNS configuration instructions
4. Example: `explainrx.yourdomain.com`

## Troubleshooting

### Build Failures

**Error: Missing dependencies**
- Solution: Verify all packages in `requirements.txt` are spelled correctly
- Check: `pip install -r requirements.txt` works locally

**Error: Module not found**
- Solution: Ensure all Python files are committed to Git
- Check: `.vercelignore` isn't excluding necessary files

### Runtime Errors

**Error: OpenAI API key not found**
- Solution: Add `OPENAI_API_KEY` in Vercel environment variables
- Redeploy after adding variables

**Error: 500 Internal Server Error**
- Check Vercel logs: Dashboard → Your Project → Deployments → Click deployment → "Runtime Logs"
- Common issue: Missing environment variables

**Error: Cold start timeouts**
- Vercel has a 10-second timeout for serverless functions
- If queries take too long, consider optimization or Vercel Pro

### View Logs

```bash
# Via CLI
vercel logs explainrx

# Or in Dashboard
Dashboard → Your Project → Deployments → Runtime Logs
```

## Production Checklist

- [ ] New `SECRET_KEY` generated for production (different from dev)
- [ ] `OPENAI_API_KEY` added to Vercel environment variables
- [ ] `.env` file is in `.gitignore` (never commit secrets!)
- [ ] Test all major features on deployed URL
- [ ] Set up error monitoring (optional: Sentry, LogRocket)
- [ ] Enable Vercel Analytics (optional)
- [ ] Configure rate limiting for API endpoints (recommended)

## Continuous Deployment

Once connected to Git:
- Push to `main` branch → Auto-deploys to production
- Push to other branches → Creates preview deployments
- Pull requests → Automatic preview URLs

## Useful Commands

```bash
# Deploy to production
vercel --prod

# View deployments
vercel ls

# View logs
vercel logs

# Remove project
vercel remove explainrx

# View environment variables
vercel env ls
```

## Support & Resources

- [Vercel Python Documentation](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
- [Vercel CLI Documentation](https://vercel.com/docs/cli)
- [Flask on Vercel Guide](https://vercel.com/guides/using-flask-with-vercel)

## Your ExplainRX URLs

After deployment, you'll have:
- **Production**: `https://explainrx.vercel.app`
- **Preview**: `https://explainrx-[branch-name]-[team].vercel.app`
- **Development**: Local testing at `http://localhost:5000`

---

**Need help?** Check the Vercel dashboard logs or run `vercel logs explainrx` for detailed error messages.
