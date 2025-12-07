# Medication Interaction Tracker - README & Build Plan

## Project Overview

A web-based Medication Interaction Tracker that helps patients identify potential interactions between prescription medications, over-the-counter drugs, supplements, foods, and lifestyle factors using natural language queries powered by LLMs.

## Technology Stack

### Backend

- **Web Framework**: Flask (Python)
- **LLM**: OpenAI GPT-4 (via OpenAI API)
- **Database APIs**: 
  - RxNorm API (for medication normalization)
  - DrugBank API (for interaction data)
  - FDA Drug Database (for official drug information)
- **Session Management**: Client-side storage (localStorage) for Vercel serverless deployment

### Frontend

- **Framework**: Flask templates with Jinja2
- **Styling**: Modern CSS (Bootstrap or Tailwind CSS recommended)
- **JavaScript**: Vanilla JS or minimal framework for interactivity

### Deployment

- **Primary**: **Vercel** (serverless Flask support - confirmed deployment platform)
- **Note**: Since Vercel uses serverless functions, user context will be stored client-side (localStorage) rather than server-side Flask sessions

## Architecture: Three-Agent System

The system uses a clear separation between deterministic database operations and LLM processing:

### 1. Query Interpreter Agent (LLM Layer)

- **Input**: User's natural language question
- **Process**: GPT-4 extracts medication names, foods, supplements, and context
- **Output**: Structured JSON query plan for the retrieval agent
- **Example Output**:
```json
{
  "medications": ["Tylenol", "Sertraline"],
  "foods": ["grapefruit juice"],
  "query_type": "interaction_check",
  "user_context": {"age": 45, "weight": 70}
}
```


### 2. Retrieval/Database Agent (Deterministic Layer)

- **Input**: Structured query from Agent 1
- **Process**: 
  - Execute API calls to RxNorm (normalize drug names)
  - Query DrugBank API (retrieve interaction data)
  - Search FDA database (official prescribing info)
  - Perform web RAG searches on drug websites
- **Output**: Structured table of interactions with severity scores, citations, metadata
- **No LLM involvement** - pure deterministic data retrieval

### 3. Explanation Agent (LLM Layer)

- **Input**: Interaction table from Agent 2
- **Process**: GPT-4 translates technical data into plain language
- **Output**: User-friendly explanation with disclaimers, flagging uncertainties
- **Grounding**: Only uses data from Agent 2 (no hallucinations)

## Project Structure

```
med-app/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
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
│   ├── index.html         # Main chat interface
│   └── profile.html       # User profile sidebar
├── static/
│   ├── css/
│   │   └── style.css      # Custom styles
│   └── js/
│       └── app.js         # Frontend interactivity
└── tests/
    ├── test_agents.py
    └── test_apis.py
```

## Key Features Implementation

### 1. Conversational Interface

- Chat-style UI with message history
- Natural language input processing
- Context-aware responses

### 2. User Profile Sidebar

- Age, weight, height input
- Existing medications list
- Health conditions
- Stored client-side (localStorage) for anonymous users

### 3. API Integrations

- **RxNorm API**: Normalize medication names to standard identifiers
- **DrugBank API**: Retrieve drug-drug interaction data
- **FDA API**: Access official drug labeling information
- **Web RAG**: Search drug manufacturer websites for additional context

### 4. Safety Features

- Prominent disclaimer on all pages
- Confidence scores for interactions
- Uncertainty flags when sources conflict
- Recommendations to consult healthcare providers

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

## API Keys Required

1. **OpenAI API Key**: Get from https://platform.openai.com/api-keys
2. **RxNorm/UMLS API**: Register at https://www.nlm.nih.gov/research/umls/
3. **DrugBank API**: Apply for access at https://go.drugbank.com/releases/latest (academic license available)

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

## Future Enhancements

- Interaction severity risk levels (High/Medium/Low)
- Confidence scores for each interaction
- User authentication (optional)
- Conversation history persistence
- Export interaction reports

## Important Notes

- **Medical Disclaimer**: This tool is for informational purposes only and does not replace professional medical advice
- **API Rate Limits**: Implement caching and rate limiting for external APIs
- **Cost Management**: Monitor OpenAI API usage (GPT-4 is more expensive than GPT-3.5)
- **Data Privacy**: User data stored only client-side (localStorage) for anonymous users

## Development Roadmap

1. Set up Flask application structure
2. Implement Agent 1 (Query Interpreter)
3. Implement Agent 2 (Retrieval Agent) with API integrations
4. Implement Agent 3 (Explanation Agent)
5. Build frontend UI with chat interface
6. Add user profile sidebar
7. Add disclaimers and safety features
8. Deploy to public URL
9. Testing and refinement

