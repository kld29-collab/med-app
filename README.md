# Medication Interaction Tracker

A conversational interface system for analyzing drug, supplement, and food interactions using natural language processing and external medication databases.

## Features

- 🗣️ **Natural Language Interface**: Ask questions in plain English about medication safety
- 🤖 **LLM-Powered Parsing**: Uses GPT to understand and extract medications, supplements, and foods from queries
- 🔍 **Multi-Database Integration**: Queries RxNorm (NIH), OpenFDA, and supports DrugBank APIs
- ⚠️ **Comprehensive Checking**: Analyzes drug-drug, drug-food, and drug-supplement interactions
- 📊 **Severity Classification**: Categorizes interactions by severity (High, Moderate, Low)
- 📝 **Plain Language Summaries**: Converts technical data into understandable explanations
- 🛡️ **Safety-First**: Always includes medical disclaimers and encourages consulting healthcare providers

## System Architecture

```
User Query → NLP Parser → Database APIs → Interaction Checker → LLM Summarizer → Response
```

1. **Query Parser** (`parser.py`): Uses OpenAI GPT to extract medications, supplements, and foods from natural language
2. **API Client** (`api_client.py`): Interfaces with RxNorm, FDA, and DrugBank APIs to fetch interaction data
3. **Interaction Checker** (`checker.py`): Analyzes combinations and identifies potential interactions
4. **Result Summarizer** (`summarizer.py`): Converts technical findings into plain language using LLM
5. **CLI Interface** (`cli.py`): Provides conversational command-line interface

## Installation

```bash
# Clone the repository
git clone https://github.com/kld29-collab/med-app.git
cd med-app

# Install dependencies
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt
```

## Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Add your OpenAI API key to `.env`:
   ```
   OPENAI_API_KEY=your_key_here
   ```
   
   Get your key from: https://platform.openai.com/api-keys

3. (Optional) Add DrugBank API key for enhanced data:
   ```
   DRUGBANK_API_KEY=your_key_here
   ```

## Usage

### Interactive Mode

Run the tracker in conversational mode:

```bash
python run_tracker.py
```

Example interaction:
```
💊 Medication Interaction Tracker - Interactive Mode

🗣️  Your question: Can I take aspirin with ibuprofen?

🔍 Parsing your question...
📋 Found: 2 medication(s), 0 supplement(s), 0 food(s)
🔬 Checking interaction databases...
📝 Generating summary...

[Results displayed here]
```

### Single Query Mode

Process a single query from command line:

```bash
python run_tracker.py "Is it safe to eat grapefruit while on statins?"
```

### Programmatic Usage

```python
from med_tracker import MedicationTracker

# Initialize the tracker
tracker = MedicationTracker(openai_api_key="your_key")

# Process a query
response = tracker.process_query(
    "Can I take vitamin D with levothyroxine?"
)
print(response)
```

## Example Queries

- "Can I take aspirin with ibuprofen?"
- "Is it safe to eat grapefruit while on statins?"
- "What supplements interact with warfarin?"
- "Can I drink alcohol while taking metformin?"
- "Should I avoid dairy when taking antibiotics?"

## Data Sources

The system queries the following public databases:

1. **RxNorm** (NIH National Library of Medicine)
   - Drug nomenclature and relationships
   - Interaction data
   - Free, no API key required

2. **OpenFDA Drug API**
   - Adverse event reports
   - Drug labeling information
   - Free, rate-limited

3. **DrugBank** (Optional)
   - Enhanced drug interaction data
   - Requires API key

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=med_tracker --cov-report=html

# Run specific test file
pytest tests/test_parser.py
```

## Architecture Details

### Module Breakdown

- **`med_tracker/parser.py`**: NLP-based query parsing using OpenAI GPT
- **`med_tracker/api_client.py`**: HTTP client for medication database APIs
- **`med_tracker/checker.py`**: Core interaction checking logic with built-in knowledge base
- **`med_tracker/summarizer.py`**: LLM-powered result summarization
- **`med_tracker/cli.py`**: Command-line interface orchestration

### Key Design Decisions

1. **Fallback Mechanisms**: All LLM features have fallback implementations that work without API keys
2. **Rate Limiting**: Respectful delays between API calls to public services
3. **Error Handling**: Graceful degradation when APIs are unavailable
4. **Medical Safety**: Always includes disclaimers and avoids giving direct medical advice

## Important Disclaimers

⚠️ **This tool is for educational and informational purposes only.**

- NOT a substitute for professional medical advice
- NOT intended to diagnose, treat, cure, or prevent any disease
- ALWAYS consult your healthcare provider before starting, stopping, or changing medications
- Interaction data may be incomplete or outdated
- Individual factors may affect how medications interact in your specific case

## Development

### Project Structure

```
med-app/
├── med_tracker/           # Main package
│   ├── __init__.py
│   ├── parser.py         # Query parsing
│   ├── api_client.py     # API integrations
│   ├── checker.py        # Interaction logic
│   ├── summarizer.py     # Result summarization
│   └── cli.py            # CLI interface
├── tests/                # Test suite
│   ├── test_parser.py
│   ├── test_api_client.py
│   ├── test_checker.py
│   ├── test_summarizer.py
│   └── test_integration.py
├── run_tracker.py        # Entry point script
├── requirements.txt      # Dependencies
└── README.md            # Documentation
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions, please open an issue on GitHub.

## Acknowledgments

- RxNorm API by NIH National Library of Medicine
- OpenFDA by U.S. Food and Drug Administration
- OpenAI GPT for natural language processing
