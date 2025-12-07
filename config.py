"""
Configuration settings for the medication interaction tracker.
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_MODEL = 'gpt-4'  # Using GPT-4 as specified
    
    # RxNorm/UMLS API Configuration
    UMLS_API_KEY = os.environ.get('UMLS_API_KEY')
    UMLS_BASE_URL = 'https://uts-ws.nlm.nih.gov/rest'
    
    # DrugBank API Configuration
    DRUGBANK_USERNAME = os.environ.get('DRUGBANK_USERNAME')
    DRUGBANK_PASSWORD = os.environ.get('DRUGBANK_PASSWORD')
    DRUGBANK_BASE_URL = 'https://go.drugbank.com'
    
    # FDA API Configuration
    FDA_API_BASE_URL = os.environ.get('FDA_API_BASE_URL', 'https://api.fda.gov')
    
    # Application Settings
    MAX_QUERY_LENGTH = 500
    MAX_MEDICATIONS_PER_QUERY = 10

