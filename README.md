# ExplainRX: Medication Interaction Tracker

A web-based medication interaction tracker that helps users identify potential drug interactions using natural language queries powered by LLMs and comprehensive drug databases.

## Quick Links

- **📖 [Getting Started](#quick-start)** - Start using the app in 5 minutes
- **🚀 [Deploy to Production](docs/DEPLOYMENT.md)** - Deploy on Vercel
- **🏥 [DrugBank Setup](docs/DRUGBANK.md)** - Initialize drug database
- **🏗️ [Architecture](docs/ARCHITECTURE.md)** - System design and data flow
- **📚 [Developer Docs](docs/dev)** - Implementation details and status

---

## Quick Start

### Prerequisites
- Python 3.9+
- API keys:
  - **OpenAI** (for GPT-4) - [Get key](https://platform.openai.com/api-keys)
  - **DrugBank** (Download account for drug data) - [Sign up](https://www.drugbank.ca)

### Local Setup (5 minutes)

1. **Clone and setup**:
```bash
cd med-app
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. **Add your API keys**:
```bash
cp .env.example .env
# Edit .env and add OPENAI_API_KEY
```

3. **Initialize DrugBank database** (one-time, ~10 minutes):
```bash
python scripts/init_drugbank_db.py
```

4. **Run the app**:
```bash
python app.py
```

Visit: http://localhost:5000

---

## Features

✅ **Natural Language Queries**
- "Can I take aspirin with ibuprofen?"
- "What are the side effects of metformin?"
- "Is there any food I should avoid with warfarin?"

✅ **Comprehensive Drug Data**
- 15,000+ drugs from DrugBank
- Drug-drug interactions
- Food-drug interactions
- FDA safety information

✅ **Fast & Reliable**
- Local SQLite database (<50ms queries)
- No rate limiting
- Offline capability

✅ **Production Ready**
- Deploy to Vercel in minutes
- Serverless compatible
- Client-side session management

---

## Technology Stack

### Backend
- **Framework**: Flask (Python)
- **LLM**: OpenAI GPT-4
- **Databases**: 
  - DrugBank (RAG via local SQLite)
  - RxNorm API (drug normalization)
  - FDA API (safety information)

### Frontend
- **Templates**: Flask + Jinja2
- **Styling**: Modern CSS
- **Interactivity**: Vanilla JavaScript

### Deployment
- **Primary**: Vercel (serverless)
- **Local**: Docker or direct Python execution

---

## Architecture

The system uses a **three-agent pipeline** with clear separation between LLM and deterministic operations:

```
User Query
    ↓
[Query Interpreter Agent] ← LLM extracts medications/foods
    ↓
[Retrieval Agent] ← Deterministic: queries DrugBank, FDA, Web
    ↓
[Explanation Agent] ← LLM translates results to plain language
    ↓
User Response
```

**Data Source Priority**:
1. **DrugBank** (comprehensive, local, fast)
2. **FDA** (official, safety-focused)
3. **Web Search** (current information)

See [Architecture](docs/ARCHITECTURE.md) for detailed diagrams and data flows.

---

## Project Structure

```
med-app/
├── docs/                      ← Documentation
│   ├── DEPLOYMENT.md         # Deploy to Vercel guide
│   ├── DRUGBANK.md           # DrugBank setup & usage
│   ├── ARCHITECTURE.md       # System design
│   └── dev/                  # Developer documentation
├── app.py                    # Main Flask application
├── config.py                 # Configuration
├── agents/                   # Three-agent system
│   ├── query_interpreter.py  # Extract medications (LLM)
│   ├── retrieval_agent.py    # Query databases (deterministic)
│   └── explanation_agent.py  # Explain results (LLM)
├── utils/                    # Utilities
│   ├── drug_apis.py         # API integrations
│   ├── drugbank_db.py       # DrugBank SQLite manager
│   ├── drugbank_loader.py   # XML parser
│   ├── session_manager.py   # User sessions
│   └── validators.py        # Input validation
├── templates/               # Flask templates
├── static/                  # CSS, JS, assets
├── tests/                   # Test suite
├── scripts/                 # Utilities
│   └── init_drugbank_db.py # Database initialization
├── data/                    # Data directory
│   ├── full_database.xml    # DrugBank download
│   └── drugbank.db          # SQLite database (auto-created)
├── requirements.txt         # Python dependencies
└── vercel.json             # Vercel configuration
```

---

## Setup Guide

### 1. Environment Variables

```bash
cp .env.example .env
```

Add to `.env`:
```
OPENAI_API_KEY=sk-proj-...your-key...
SECRET_KEY=generate-with: python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialize DrugBank Database

```bash
python scripts/init_drugbank_db.py
```

**Note**: First run takes 5-30 minutes to parse the 1.5GB XML file. Subsequent runs are instant.

### 4. Run Locally

```bash
python app.py
```

Visit: http://localhost:5000


---

## Deployment

### Quick Deploy to Vercel

1. **Push to GitHub** (if not already)
```bash
git add .
git commit -m "Ready for production"
git push origin main
```

2. **Initialize database locally** (to avoid Vercel timeout):
```bash
python scripts/init_drugbank_db.py
git add data/drugbank.db
git commit -m "Add initialized database"
git push
```

3. **Deploy via Vercel**:
   - Go to https://vercel.com/new
   - Import your repository
   - Set root directory: `med-app`
   - Add environment variables (see [Deployment Guide](docs/DEPLOYMENT.md))
   - Click Deploy

For detailed instructions, see **[Deployment Guide](docs/DEPLOYMENT.md)**.

---

## Testing

Run the test suite:

```bash
# All tests
python -m pytest tests/

# Specific test file
python -m pytest tests/test_comprehensive.py

# With coverage
python -m pytest tests/ --cov=utils --cov=agents
```

Available test files:
- `tests/test_comprehensive.py` - End-to-end query tests
- `tests/test_query.py` - Individual drug query tests
- `tests/test_drugbank_integration.py` - DrugBank database tests
- `tests/test_agents.py` - Agent unit tests
- `tests/test_apis.py` - API integration tests

---

## Configuration

Edit `config.py` to customize:

```python
OPENAI_MODEL = "gpt-4"           # LLM model
MAX_DRUGS_PER_QUERY = 5          # Limit simultaneous drugs
SESSION_TIMEOUT = 3600           # Session duration (seconds)
DEBUG_MODE = False               # Enable debug logging
```

---

## Common Issues & Solutions

### "DrugBank database not initialized"
```bash
python scripts/init_drugbank_db.py
```

### Drug name not found
- The system includes **fuzzy matching** (e.g., "aspirin" → "Acetylsalicylic acid")
- Try searching for the drug: use `search_drugbank()` method
- Check debug logs for exact database names

### Slow deployment on Vercel
- Initialize the database locally first (see [Deployment Guide](docs/DEPLOYMENT.md))
- Vercel has a 10-second timeout on first request

### API key errors
- Verify `.env` file has correct keys
- Check OPENAI_API_KEY format (starts with `sk-proj-`)
- Don't commit `.env` file to Git

---

## Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test with output
pytest tests/test_comprehensive.py -v -s

# Run tests with coverage report
pytest --cov=utils --cov=agents tests/
```

### Debugging

Enable debug logging:
```python
# In config.py
DEBUG_MODE = True
```

Watch console output for `[DEBUG]`, `[INFO]`, `[WARNING]` messages.

### Adding New Features

1. **New data source?** Add to `utils/drug_apis.py`
2. **New agent logic?** Update `agents/retrieval_agent.py`
3. **New UI element?** Edit `templates/index.html`
4. **New tests?** Add to `tests/`

See [Developer Docs](docs/dev) for detailed architecture.

---

## Documentation

- **[Deployment Guide](docs/DEPLOYMENT.md)** - Deploy to Vercel or run locally
- **[DrugBank Setup](docs/DRUGBANK.md)** - Initialize and use drug database
- **[System Architecture](docs/ARCHITECTURE.md)** - Design diagrams and data flows
- **[Implementation Details](docs/dev/IMPLEMENTATION_SUMMARY.md)** - Technical overview
- **[Completion Status](docs/dev/COMPLETION_STATUS.md)** - Feature checklist

---

## Performance

| Operation | Time | Method |
|-----------|------|--------|
| Drug search | ~50ms | SQLite |
| Interaction lookup | ~50ms | SQLite |
| API normalization | ~500ms | RxNorm API |
| FDA safety info | ~500ms | FDA API |
| Web search | ~2000ms | SerpAPI |
| **Total response** | **~3 seconds** | Combined |

---

## Support

- 📖 Check the [docs/](docs/) folder
- 🐛 Check console output for debug messages
- 🔍 Review test files for usage examples
- 💬 OpenAI API status: https://status.openai.com

---

## License

This project uses:
- **DrugBank** (Download account) - Academic/research use
- **OpenAI API** - Subject to OpenAI terms
- **FDA Data** - Public domain
- **RxNorm** - Public domain (UMLS)

---

## Next Steps

✅ Local setup complete?
- Test a query: "Can I take aspirin with ibuprofen?"

✅ Ready to deploy?
- Follow [Deployment Guide](docs/DEPLOYMENT.md)
- Deploy to Vercel in ~5 minutes

✅ Want to customize?
- Check [System Architecture](docs/ARCHITECTURE.md) for design
- See [Developer Docs](docs/dev) for implementation details

---

**Built with ❤️ for medication safety**
