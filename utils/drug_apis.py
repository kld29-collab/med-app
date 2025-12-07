"""
Drug API utilities for interacting with RxNorm, DrugBank, and FDA databases.
This is the deterministic layer - no LLM involvement.
"""
import requests
import time
from typing import List, Dict, Optional
from config import Config


class DrugAPIClient:
    """Client for interacting with drug databases."""
    
    def __init__(self):
        """Initialize API clients."""
        self.umls_api_key = Config.UMLS_API_KEY
        self.drugbank_username = Config.DRUGBANK_USERNAME
        self.drugbank_password = Config.DRUGBANK_PASSWORD
        self.fda_base_url = Config.FDA_API_BASE_URL
    
    def normalize_drug_name_rxnorm(self, drug_name: str) -> Optional[Dict]:
        """
        Normalize drug name using RxNorm API.
        
        Args:
            drug_name: Common or brand name of the drug
        
        Returns:
            Dictionary with normalized drug information or None
        """
        if not self.umls_api_key:
            return None
        
        try:
            # RxNorm search endpoint
            url = f"{Config.UMLS_BASE_URL}/search/current"
            params = {
                "string": drug_name,
                "searchType": "exact",
                "inputType": "sourceUi",
                "sabs": "RXNORM",
                "apiKey": self.umls_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("result") and data["result"].get("results"):
                result = data["result"]["results"][0]
                # Get normalized name, fallback to original drug_name if not available
                normalized_name = result.get("name") or drug_name
                return {
                    "rxcui": result.get("ui"),
                    "name": result.get("name"),
                    "original_name": drug_name,  # Always preserve original name
                    "normalized_name": normalized_name,
                    "source": "RxNorm"
                }
            
            return None
            
        except Exception as e:
            print(f"Error normalizing drug name {drug_name}: {str(e)}")
            return None
    
    def get_drug_interactions_drugbank(self, drug_names: List[str]) -> List[Dict]:
        """
        Get drug interactions from DrugBank API.
        
        Args:
            drug_names: List of normalized drug names
        
        Returns:
            List of interaction dictionaries
        """
        if not self.drugbank_username or not self.drugbank_password:
            return []
        
        interactions = []
        
        try:
            # Note: DrugBank API requires authentication and has specific endpoints
            # This is a simplified example - actual implementation depends on DrugBank API version
            base_url = f"{Config.DRUGBANK_BASE_URL}/releases/latest"
            
            # For each drug, check interactions with others
            for i, drug1 in enumerate(drug_names):
                for drug2 in drug_names[i+1:]:
                    # DrugBank API call would go here
                    # This is a placeholder structure
                    interaction = {
                        "drug1": drug1,
                        "drug2": drug2,
                        "severity": "unknown",  # Would be retrieved from API
                        "description": "Interaction data from DrugBank",
                        "source": "DrugBank",
                        "confidence": "medium"
                    }
                    interactions.append(interaction)
            
            return interactions
            
        except Exception as e:
            print(f"Error getting DrugBank interactions: {str(e)}")
            return []
    
    def get_fda_drug_info(self, drug_name: str) -> Optional[Dict]:
        """
        Get drug information from FDA API.
        
        Args:
            drug_name: Name of the drug
        
        Returns:
            Dictionary with FDA drug information or None
        """
        try:
            # FDA Drug Labeling API
            url = f"{self.fda_base_url}/drug/label.json"
            params = {
                "search": f"openfda.brand_name:{drug_name}",
                "limit": 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("results") and len(data["results"]) > 0:
                result = data["results"][0]
                openfda = result.get("openfda", {})
                
                # Safely extract brand_name - handle empty lists
                brand_name_list = openfda.get("brand_name", [])
                brand_name = brand_name_list[0] if brand_name_list else drug_name
                
                # Safely extract generic_name - handle empty lists
                generic_name_list = openfda.get("generic_name", [])
                generic_name = generic_name_list[0] if generic_name_list else ""
                
                return {
                    "drug_name": drug_name,
                    "brand_name": brand_name,
                    "generic_name": generic_name,
                    "warnings": result.get("warnings", []),
                    "source": "FDA"
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting FDA info for {drug_name}: {str(e)}")
            return None
    
    def search_drug_websites(self, drug_name: str) -> List[Dict]:
        """
        Perform web search for drug information (RAG approach).
        This would typically use a search API or web scraping.
        
        Args:
            drug_name: Name of the drug
        
        Returns:
            List of search results with drug information
        """
        # Placeholder for web RAG implementation
        # In production, this would use a search API (e.g., Google Custom Search, Bing)
        # or scrape trusted drug information websites
        
        return [
            {
                "drug_name": drug_name,
                "source": "web_search",
                "snippet": f"Information about {drug_name} from web sources",
                "url": "",
                "confidence": "low"
            }
        ]


def normalize_medications(medications: List[str], api_client: DrugAPIClient) -> List[Dict]:
    """
    Normalize a list of medication names using RxNorm.
    
    Args:
        medications: List of medication names (brand or common names)
        api_client: DrugAPIClient instance
    
    Returns:
        List of normalized medication dictionaries
    """
    normalized = []
    
    for med in medications:
        normalized_med = api_client.normalize_drug_name_rxnorm(med)
        if normalized_med:
            normalized.append(normalized_med)
        else:
            # Fallback: use original name if normalization fails
            normalized.append({
                "original_name": med,
                "normalized_name": med,
                "source": "fallback"
            })
        
        # Rate limiting
        time.sleep(0.5)
    
    return normalized

