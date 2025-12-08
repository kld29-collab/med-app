# DrugBank Integration Guide (RAG Approach)

## Overview

Your medication tracker now integrates with **DrugBank** using a **RAG (Retrieval-Augmented Generation)** approach with your Download account. This gives you access to comprehensive drug interaction data without requiring a Web Services API subscription.

## How It Works

### Architecture

```
DrugBank XML (1.5GB)
        ↓
   [XML Parser] (drugbank_loader.py)
        ↓
   [SQLite DB] (drugbank.db)
        ↓
   [Query API] (drugbank_db.py)
        ↓
   [DrugAPIClient] (drug_apis.py)
        ↓
   [Your App]
```

1. **XML Parser** (`drugbank_loader.py`): Efficiently parses the large DrugBank XML file using iterparse for memory efficiency
2. **SQLite Database** (`drugbank_db.py`): Stores structured data with indexed lookups for fast queries
3. **Query API**: Provides convenient methods to search drugs and retrieve interactions
4. **Integration**: Seamlessly integrated into your existing `DrugAPIClient`

## Setup

### Step 1: Initialize the Database

The first time you run the app (or when deploying), initialize the SQLite database from the XML file:

```bash
python scripts/init_drugbank_db.py
```

**What to expect:**
- Processing time: 5-30 minutes (depending on system performance)
- Output size: ~2-3 GB SQLite database
- Progress: Console will show progress every 5,000 drugs

**Note:** This only needs to run once. After that, the database is reused.

### Step 2: Use in Your App

The `DrugAPIClient` automatically initializes the database on first use:

```python
from utils.drug_apis import DrugAPIClient

client = DrugAPIClient()

# Search for a drug
results = client.search_drugbank("aspirin")

# Get drug details
drug_info = client.get_drug_details_drugbank("aspirin")

# Get drug-drug interactions
interactions = client.get_drug_interactions_drugbank(["aspirin", "ibuprofen"])

# Get food interactions
food_interactions = client.get_food_interactions_drugbank("aspirin")
```

## Available Methods

### `DrugAPIClient` Methods

#### `search_drugbank(search_term: str) -> List[Dict]`
Search for drugs by partial name match.

```python
results = client.search_drugbank("aspirin")
# Returns: [{"id": "DB00945", "name": "Aspirin", ...}, ...]
```

#### `get_drug_details_drugbank(drug_name: str) -> Optional[Dict]`
Get detailed information about a specific drug.

```python
drug = client.get_drug_details_drugbank("aspirin")
# Returns: {
#   "id": "DB00945",
#   "name": "Aspirin",
#   "description": "...",
#   "indication": "...",
#   "mechanism_of_action": "...",
#   "toxicity": "..."
# }
```

#### `get_drug_interactions_drugbank(drug_names: List[str]) -> List[Dict]`
Get interactions between multiple drugs.

```python
interactions = client.get_drug_interactions_drugbank(["aspirin", "warfarin"])
# Returns: [{
#   "drug1_id": "DB00945",
#   "drug2_id": "DB00682",
#   "drug2_name": "Warfarin",
#   "description": "Increased anticoagulant effect...",
#   "source": "DrugBank",
#   "confidence": "high"
# }, ...]
```

#### `get_food_interactions_drugbank(drug_name: str) -> List[str]`
Get food interactions for a drug.

```python
interactions = client.get_food_interactions_drugbank("aspirin")
# Returns: [
#   "Alcohol may increase the risk of gastrointestinal bleeding...",
#   "..."
# ]
```

## Data Structure

### Drugs Table
```sql
CREATE TABLE drugs (
    id TEXT PRIMARY KEY,              -- DrugBank ID
    name TEXT NOT NULL,               -- Drug name
    description TEXT,                 -- Full description
    indication TEXT,                  -- What it's used for
    mechanism_of_action TEXT,         -- How it works
    toxicity TEXT,                    -- Toxicity information
    created_at TIMESTAMP
);
```

### Drug Interactions Table
```sql
CREATE TABLE drug_interactions (
    id INTEGER PRIMARY KEY,
    drug_id TEXT,                     -- First drug
    interacting_drug_id TEXT,         -- Second drug
    interacting_drug_name TEXT,       -- Name of second drug
    description TEXT,                 -- Interaction description
    created_at TIMESTAMP
);
```

### Food Interactions Table
```sql
CREATE TABLE food_interactions (
    id INTEGER PRIMARY KEY,
    drug_id TEXT,                     -- Drug
    description TEXT,                 -- Food interaction description
    created_at TIMESTAMP
);
```

## File Organization

```
med-app/
├── data/
│   ├── drugbank.xsd                 # Schema (reference)
│   ├── full_database.xml            # Raw DrugBank data (1.5GB)
│   └── drugbank.db                  # SQLite database (created on init)
├── scripts/
│   └── init_drugbank_db.py          # Database initialization script
└── utils/
    ├── drugbank_loader.py           # XML parser
    ├── drugbank_db.py               # Database manager
    └── drug_apis.py                 # API client (updated)
```

## Performance Notes

- **Parsing**: ~5-30 minutes for first initialization
- **Database Size**: ~2-3 GB
- **Query Speed**: < 100ms for most queries
- **Memory**: ~50-100 MB during operation
- **No Rate Limiting**: Unlimited local queries

## Troubleshooting

### Database initialization takes too long
- This is normal for the first run. The 1.5GB XML file needs to be parsed.
- You can check progress in the console output
- Consider running this on a faster machine if possible

### "DrugBank database not initialized" warning
- Run: `python scripts/init_drugbank_db.py`
- Ensure `data/full_database.xml` exists
- Check that the database has write permissions in the `data/` directory

### Slow queries
- The database creates indexes automatically
- If queries are still slow, the database may not be properly indexed
- Try recreating the database: `rm data/drugbank.db && python scripts/init_drugbank_db.py`

### Missing data in queries
- The XMLparser extracts specific elements from the DrugBank schema
- Some drugs may not have all fields populated in DrugBank
- Check `data/drugbank.xsd` for the schema structure

## Integration with Your Retrieval Agent

The retrieval agent automatically uses DrugBank when available:

```python
# In agents/retrieval_agent.py
from utils.drug_apis import DrugAPIClient

api_client = DrugAPIClient()

# Get interactions from DrugBank (RAG approach)
interactions = api_client.get_drug_interactions_drugbank(drug_names)

# Plus FDA and web search for comprehensive coverage
fda_data = api_client.get_fda_drug_info(drug_name)
web_results = api_client.search_drug_websites(drug_name)
```

## Future Enhancements

Potential improvements:
- Add biotech drug filtering
- Extract additional ADME properties (absorption, distribution, etc.)
- Implement fuzzy matching for better drug name searching
- Add batch processing for multiple drugs
- Cache frequently accessed queries
- Export interaction matrices as CSV/JSON

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review console output for debug messages (marked with `[DEBUG]`, `[INFO]`, `[WARNING]`)
3. Verify the XML file exists and is readable
4. Ensure you have adequate disk space for the database
