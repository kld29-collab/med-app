# DrugBank RAG Integration - Architecture Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        YOUR APPLICATION                          │
│                                                                   │
│  app.py (Flask)                                                  │
│       ↓                                                           │
│  agents/                                                         │
│  ├── query_interpreter.py  (LLM: Extract drugs from query)     │
│  ├── retrieval_agent.py    (Get interactions from DB)          │
│  └── explanation_agent.py  (LLM: Explain results)              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     DRUG API CLIENT LAYER                        │
│                    (utils/drug_apis.py)                         │
│                                                                   │
│  DrugAPIClient()                                                │
│  ├── normalize_drug_name_rxnorm()    (RxNorm API)             │
│  ├── get_drug_interactions_drugbank() (DrugBank DB) ⭐        │
│  ├── get_drug_details_drugbank()     (DrugBank DB) ⭐         │
│  ├── get_food_interactions_drugbank()(DrugBank DB) ⭐         │
│  ├── search_drugbank()               (DrugBank DB) ⭐         │
│  ├── get_fda_drug_info()             (FDA API)               │
│  └── search_drug_websites()          (SerpAPI)               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┴──────────────────┐
        ↓                                        ↓
   ┌─────────────┐                      ┌──────────────────┐
   │  RxNorm API │                      │  DrugBank RAG    │
   │  (Public)   │                      │  (Local SQLite)  │
   │             │                      │                  │
   │ Normalize   │                      │ search_drugbank()│
   │ drug names  │                      │ get_details()    │
   └─────────────┘                      │ get_interactions│
                                        │ food_interact() │
                                        └──────────────────┘
                                               ↓
                                        ┌──────────────────┐
                                        │   drugbank.db    │
                                        │  (SQLite, 3GB)   │
                                        │                  │
                                        │  DRUGS table     │
                                        │  ├─ 15,000+ rows │
                                        │  ├─ indexed      │
                                        │  └─ full details │
                                        │                  │
                                        │  INTERACTIONS    │
                                        │  ├─ drug-drug    │
                                        │  └─ drug-food    │
                                        └──────────────────┘
                                               ↑
                                        (created once by)
                                               ↓
                                   ┌───────────────────────┐
                                   │ init_drugbank_db.py   │
                                   │                       │
                                   │ Parses XML once       │
                                   │ Creates DB indices    │
                                   │ Handles 1.5GB file    │
                                   └───────────────────────┘
                                               ↑
                                               │
                                   ┌───────────────────────┐
                                   │ full_database.xml     │
                                   │   (DrugBank)          │
                                   │   1.5 GB              │
                                   │   15,000+ drugs       │
                                   │   (Download Account)  │
                                   └───────────────────────┘
```

## Data Processing Pipeline

```
USER QUERY
   │
   ├─→ [Query Interpreter] (LLM)
   │       "What interactions does aspirin have?"
   │
   ├─→ Extract: ["aspirin"]
   │
   ├─→ [Retrieval Agent] (Deterministic)
   │       │
   │       ├─→ Normalize: RxNorm → "aspirin"
   │       │
   │       ├─→ Lookup: DrugBank DB
   │       │       │
   │       │       ├─→ search_drugbank("aspirin")
   │       │       ├─→ get_drug_details_drugbank("aspirin")
   │       │       ├─→ get_drug_interactions_drugbank(["aspirin"])
   │       │       └─→ get_food_interactions_drugbank("aspirin")
   │       │
   │       ├─→ FDA Info: FDA API
   │       │
   │       └─→ Web Search: SerpAPI
   │
   ├─→ Combine Results
   │       {
   │         "drug_details": {...},
   │         "interactions": [...],
   │         "food_interactions": [...],
   │         "fda_warnings": [...],
   │         "web_results": [...]
   │       }
   │
   ├─→ [Explanation Agent] (LLM)
   │       Transform to plain language
   │       Add disclaimers
   │
   └─→ USER RESPONSE
       "Aspirin can interact with warfarin,
        increasing bleeding risk. Avoid alcohol
        consumption..."
```

## File Organization

```
med-app/
│
├── data/                          ← DrugBank files
│   ├── full_database.xml          ← 1.5GB XML (your download)
│   ├── drugbank.xsd               ← Schema reference
│   └── drugbank.db                ← SQLite (auto-created)
│
├── utils/                         ← Drug APIs
│   ├── drugbank_loader.py         ← XML→Python
│   ├── drugbank_db.py             ← Python→SQLite
│   ├── drug_apis.py               ← Unified API
│   ├── session_manager.py
│   └── validators.py
│
├── scripts/                       ← Utilities
│   └── init_drugbank_db.py        ← Create DB (run once)
│
├── agents/                        ← Core logic
│   ├── query_interpreter.py       ← LLM
│   ├── retrieval_agent.py         ← Uses drug_apis.py
│   └── explanation_agent.py       ← LLM
│
├── templates/                     ← Frontend
├── static/                        ← Assets
├── tests/                         ← Test suite
│
├── app.py                         ← Main Flask app
├── config.py                      ← Configuration
├── IMPLEMENTATION_SUMMARY.md      ← This overview
└── DRUGBANK_INTEGRATION.md        ← Detailed guide
```

## Query Execution Timeline

```
User submits: "Do aspirin and ibuprofen interact?"
│
├─ T+0ms    Received in app.py
├─ T+5ms    Query Interpreter (LLM) extracts ["aspirin", "ibuprofen"]
├─ T+100ms  Retrieval Agent starts:
│
│   DrugBank DB Queries (parallelizable):
│   ├─ search_drugbank("aspirin")          [< 50ms]
│   ├─ search_drugbank("ibuprofen")        [< 50ms]
│   ├─ get_interactions(["aspirin",        [< 50ms]
│   │                    "ibuprofen"])
│   ├─ get_food_interactions("aspirin")    [< 30ms]
│   └─ get_food_interactions("ibuprofen")  [< 30ms]
│
├─ T+200ms  FDA API calls (parallel)       [~1000ms]
├─ T+300ms  Web search (parallel)          [~2000ms]
│
├─ T+2300ms Results combined by Retrieval Agent
├─ T+2400ms Explanation Agent (LLM) formats response
├─ T+2500ms Response sent to user
│
└─ Total: ~2.5 seconds (mostly waiting for external APIs)
           DrugBank queries: negligible overhead
```

## Performance Comparison

```
┌──────────────────────────────────────────────────────────────┐
│ Data Source        │ Method  │ Query Time │ Cost │ Offline   │
├──────────────────────────────────────────────────────────────┤
│ RxNorm             │ API     │ ~500ms     │ $0   │ No        │
│ DrugBank API       │ API     │ ~1000ms    │ $$$$ │ No        │
│ DrugBank (RAG)  ✓  │ SQLite  │ ~50ms      │ $0   │ Yes       │
│ FDA                │ API     │ ~500ms     │ $0   │ No        │
│ Web Search         │ API     │ ~2000ms    │ $    │ No        │
└──────────────────────────────────────────────────────────────┘

✓ = What you're using now
```

## Initialization Flow

```
First Run (or first call to app):

app.py → DrugAPIClient()
         │
         └→ _initialize_drugbank_db()
            │
            ├─ Check: drugbank.db exists?
            │  ├─ YES → connect() ✓ Done (instant)
            │  └─ NO → Continue...
            │
            ├─ Check: full_database.xml exists?
            │  └─ YES → Continue...
            │
            ├─ Create database:
            │  ├─ DrugBankLoader.load()
            │  │  └─ Parse XML (5-30 min)
            │  │
            │  ├─ DrugBankDatabase._create_tables()
            │  │  └─ Create schema & indices
            │  │
            │  └─ DrugBankDatabase._load_drugs()
            │     └─ Populate database
            │
            └─ Return connected DrugBankDatabase instance
               └─ app ready to use ✓


Subsequent Runs:

app.py → DrugAPIClient()
         │
         └→ _initialize_drugbank_db()
            │
            ├─ Check: drugbank.db exists? → YES
            │
            ├─ Connect to existing database
            │
            └─ Ready (instant) ✓
```

## Key Advantages of RAG Approach

```
✅ Fast       : Local SQLite queries (~50ms)
✅ Cheap      : No per-request API costs
✅ Reliable   : No rate limiting, no API downtime
✅ Offline    : Works without internet
✅ Complete   : 15,000+ drugs with full details
✅ Scalable   : Query unlimited interactions
✅ Flexible   : Can customize DB schema
✅ Integrated : Seamless with your LLM pipeline
```

## Summary

Your medication tracker now has a **complete, production-ready RAG system** using DrugBank's Download account. The architecture provides:

- **Fast queries** from local SQLite database
- **Comprehensive data** from 15,000+ drugs  
- **No API costs** or rate limiting
- **Seamless integration** with your LLM agents
- **Offline capability** for critical functionality

The system is ready to use. Just initialize the database once with `python scripts/init_drugbank_db.py` and enjoy unlimited drug interactions queries!
