# Quick Deploy to Vercel - ExplainRX

## Option 1: Deploy via Web (Recommended for First Time)

1. **Go to**: https://vercel.com/new
2. **Import Git Repository**: Select your `bigdatahw` repo
3. **Set Root Directory**: `med-app` (if applicable)
4. **Add Environment Variables**:
   - `OPENAI_API_KEY`: Your OpenAI key
   - `SECRET_KEY`: Generate new with: `python3 -c "import secrets; print(secrets.token_hex(32))"`
5. **Click Deploy** 🚀
6. **Your URL**: `https://explainrx.vercel.app` (or similar)

## Option 2: Deploy via CLI (For Updates)

```bash
# Install Vercel CLI (one time)
npm install -g vercel

# Login
vercel login

# Deploy
cd "/Users/kristendelancey/my-repo/Med App/med-app"
vercel --prod
```

## Environment Variables Needed

### Required:
- `OPENAI_API_KEY` - Your OpenAI API key
- `SECRET_KEY` - Generate new for production!

### Optional:
- `DRUGBANK_USERNAME` - For DrugBank integration
- `DRUGBANK_PASSWORD` - For DrugBank integration

## After Deploy

✅ Your app will be live at: `https://explainrx.vercel.app`  
✅ Every push to `main` auto-deploys  
✅ Other branches create preview URLs

## Test Your Deployment

Visit your URL and try:
- "Can I take aspirin with ibuprofen?"
- "What are the side effects of metformin?"

## Troubleshooting

**Can't find app?**
- Check root directory is set to `med-app`

**500 Error?**
- Check environment variables are set
- View logs: Vercel Dashboard → Your Project → Runtime Logs

**Need help?**
- See full guide in `DEPLOYMENT.md`
