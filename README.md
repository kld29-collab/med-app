# Medication Interaction Tracker

A web-based Medication Interaction Tracker that helps patients identify potential interactions between prescription medications, over-the-counter drugs, supplements, foods, and lifestyle factors using natural language queries powered by LLMs.

## Technology Stack

### Backend
- **Web Framework**: Flask (Python)
- **LLM**: OpenAI GPT-4 (via OpenAI API)
- **Database APIs**: 
  - RxNorm API (for medication normalization)
  - **DrugBank Database** (RAG approach - local SQLite from Download account)
  - FDA Drug Database (for official drug information)
  - Web Search (SerpAPI for additional data)
- **Session Management**: Client-side storage (localStorage) for Vercel serverless deployment

### Frontend
- **Framework**: Flask templates with Jinja2
- **Styling**: Modern CSS with responsive design
- **JavaScript**: Vanilla JS for interactivity

### Deployment
- **Primary**: **Vercel** (serverless Flask support)
- **Note**: User context stored client-side (localStorage) for serverless compatibility

## Architecture: Three-Agent System

The system uses a clear separation between deterministic database operations and LLM processing:

### 1. Query Interpreter Agent (LLM Layer)
- Extracts medication names, foods, supplements from natural language
- Outputs structured JSON query plan

### 2. Retrieval/Database Agent (Deterministic Layer)
- Executes API calls to RxNorm, DrugBank, FDA
- Returns structured interaction tables
- **No LLM involvement** - pure deterministic data retrieval

### 3. Explanation Agent (LLM Layer)
- Translates technical data into plain language
- Flags uncertainties and includes disclaimers
- Grounded in retrieved data only

## Project Structure

```
med-app/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── vercel.json
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── agents/
│   ├── __init__.py
│   ├── query_interpreter.py  # Agent 1: Query interpretation
│   ├── retrieval_agent.py    # Agent 2: Database queries (deterministic)
│   └── explanation_agent.py  # Agent 3: Plain language explanations
├── utils/
│   ├── __init__.py
│   ├── drug_apis.py       # RxNorm, DrugBank, FDA API wrappers
│   ├── session_manager.py # User context management
│   └── validators.py      # Input validation
├── templates/
│   ├── base.html          # Base template
│   └── index.html         # Main chat interface
├── static/
│   ├── css/
│   │   └── style.css      # Custom styles
│   └── js/
│       └── app.js         # Frontend interactivity
└── tests/
    ├── test_agents.py
    └── test_apis.py
```

## Setup Instructions

### Prerequisites
- Python 3.9+
- API keys for:
  - OpenAI (GPT-4)
  - RxNorm (UMLS account)
  - DrugBank (academic/research license)
  - FDA API (free, no key needed)

### Installation Steps

1. **Clone and setup environment**:
```bash
cd med-app
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Run the application**:
```bash
python app.py
```

4. **Access the app**:
- Local: http://localhost:5000
- Deploy to Vercel for public access

## Data Sources

### RxNorm API
**Purpose**: Drug name normalization and RxCUI identifier resolution  
**Status**: ✅ Working  
**API Used**: `/rxcui.json` (exact match) and `/approximateTerm.json` (fuzzy match)  
**Note**: RxNorm's `/interaction/` endpoints (referenced in older documentation) have been **deprecated by the NLM** and are no longer available.

### FDA Drug Labels (OpenFDA)
**Purpose**: Contraindications, warnings, precautions, and documented drug interactions  
**Status**: ✅ Working  
**API**: https://api.fda.gov/drug/label.json  
**Authentication**: None required (public API)  
**Data Retrieved**: Brand names, generic names, warnings, contraindications, precautions, documented interactions

### Web Search (SerpAPI)
**Purpose**: Current drug interaction information and clinical evidence  
**Status**: ✅ Working  
**Note**: Used as the primary interaction data source due to RxNorm interaction API deprecation  
**Configuration**: Requires `SERPAPI_KEY` environment variable

### DrugBank API (Optional)
**Purpose**: Professional-grade drug interaction database with 13,000+ drugs  
**Status**: Not yet implemented (framework exists)  
**Requires**: Paid subscription credentials (username/password)  
**Benefits**: Comprehensive interaction data with detailed pharmacokinetics

## API Migration Notes

**RxNorm Interaction API Deprecation**:
- The NLM has deprecated the `/interaction/interaction.json` and `/interaction/list.json` endpoints
- Older NIH documentation references these endpoints, but they are no longer maintained
- **Current Solution**: Drug interaction data is retrieved from FDA labels + web search
- These sources provide evidence-based, clinically relevant interaction information



## Example User Flow

```
USER: "Can I take Tylenol with my antidepressant?"

→ Agent 1 (LLM): Extracts medications, generates query plan
   Output: {"medications": ["Tylenol", "antidepressant"], ...}

→ Agent 2 (Deterministic): Queries databases
   - RxNorm: Normalizes "Tylenol" → "acetaminophen"
   - DrugBank: Checks interactions
   - Returns structured table

→ Agent 3 (LLM): Generates plain-language explanation
   Output: "Tylenol (acetaminophen) is generally safe with most 
   antidepressants, but you should consult your doctor..."
```

## Important Notes

- **Medical Disclaimer**: This tool is for informational purposes only and does not constitute medical advice. Always consult with a qualified healthcare provider.
- **API Rate Limits**: Implement caching and rate limiting for external APIs
- **Cost Management**: Monitor OpenAI API usage (GPT-4 is more expensive than GPT-3.5)
- **Data Privacy**: User data stored only client-side (localStorage) for anonymous users

## Deployment to Vercel

1. Install Vercel CLI: `npm i -g vercel`
2. Run `vercel` in the project directory
3. Configure environment variables in Vercel dashboard
4. Deploy: `vercel --prod`

## Development Roadmap

- [x] Set up Flask application structure
- [x] Implement Agent 1 (Query Interpreter)
- [x] Implement Agent 2 (Retrieval Agent) with API integrations
- [x] Implement Agent 3 (Explanation Agent)
- [x] Build frontend UI with chat interface
- [x] Add user profile sidebar
- [x] Add disclaimers and safety features
- [ ] Deploy to public URL
- [ ] Testing and refinement
