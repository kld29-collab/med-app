"""
Drug API utilities for interacting with RxNorm, DrugBank, and FDA databases.
This is the deterministic layer - no LLM involvement.

NOTE: RxNorm API is used ONLY for drug name normalization and RxCUI identifier resolution.
RxNorm's /interaction/ endpoints (referenced in older NIH documentation) have been deprecated
and are no longer available. Drug interaction data is retrieved from DrugBank database (RAG approach),
FDA drug labels (OpenFDA), and web search results instead.
"""
import requests
import time
from typing import List, Dict, Optional
from pathlib import Path
from config import Config
from .drugbank_db import DrugBankDatabase


class DrugAPIClient:
    """Client for interacting with drug databases."""
    
    def __init__(self):
        """Initialize API clients."""
        self.rxnorm_base_url = Config.RXNORM_BASE_URL
        self.drugbank_username = Config.DRUGBANK_USERNAME
        self.drugbank_password = Config.DRUGBANK_PASSWORD
        self.fda_base_url = Config.FDA_API_BASE_URL
        
        # Initialize DrugBank database
        self.drugbank_db = self._initialize_drugbank_db()
    
    def _initialize_drugbank_db(self) -> Optional[DrugBankDatabase]:
        """
        Initialize DrugBank database connection.
        
        Returns:
            DrugBankDatabase instance or None if initialization fails
        """
        import sys
        try:
            # Paths for database and XML file
            base_path = Path(__file__).parent.parent
            db_file = base_path / "data" / "drugbank.db"
            xml_file = base_path / "data" / "full_database.xml"
            
            # Create database if it doesn't exist
            if not db_file.exists():
                if xml_file.exists():
                    print(f"[INFO] Creating DrugBank database from XML...", file=sys.stderr)
                    db = DrugBankDatabase(str(db_file), str(xml_file))
                    if db.initialize():
                        print(f"[INFO] DrugBank database created successfully", file=sys.stderr)
                        return db
                    else:
                        print(f"[WARNING] Failed to create DrugBank database", file=sys.stderr)
                        return None
                else:
                    print(f"[WARNING] DrugBank XML file not found at {xml_file}", file=sys.stderr)
                    return None
            
            # Connect to existing database
            db = DrugBankDatabase(str(db_file))
            if db.connect():
                print(f"[INFO] Connected to existing DrugBank database", file=sys.stderr)
                return db
            else:
                print(f"[WARNING] Failed to connect to DrugBank database", file=sys.stderr)
                return None
                
        except Exception as e:
            print(f"[WARNING] Error initializing DrugBank database: {str(e)}", file=sys.stderr)
            return None
    
    def normalize_drug_name_rxnorm(self, drug_name: str) -> Optional[Dict]:
        """
        Normalize drug name using RxNorm public REST API (no authentication required).
        
        Args:
            drug_name: Common or brand name of the drug
        
        Returns:
            Dictionary with normalized drug information or None
        """
        import sys
        try:
            # Try exact match first using RxNorm's public API
            url = f"{self.rxnorm_base_url}/rxcui.json"
            params = {"name": drug_name}
            
            print(f"[DEBUG] RxNorm exact match request: {url} with params {params}", file=sys.stderr)
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            print(f"[DEBUG] RxNorm exact match response: {data}", file=sys.stderr)
            
            # If exact match found
            if data.get("idGroup") and data["idGroup"].get("rxnormId"):
                rxcui = data["idGroup"]["rxnormId"][0]
                
                # Get the drug name from RxCUI
                name_url = f"{self.rxnorm_base_url}/rxcui/{rxcui}/property.json"
                name_response = requests.get(name_url, params={"propName": "RxNorm Name"}, timeout=10)
                name_data = name_response.json()
                
                drug_name_normalized = drug_name
                if name_data.get("propConceptGroup") and name_data["propConceptGroup"].get("propConcept"):
                    drug_name_normalized = name_data["propConceptGroup"]["propConcept"][0].get("propValue", drug_name)
                
                result = {
                    "rxcui": rxcui,
                    "name": drug_name_normalized,
                    "original_name": drug_name,
                    "normalized_name": drug_name_normalized,
                    "source": "RxNorm"
                }
                print(f"[DEBUG] Exact match found for {drug_name}: {result}", file=sys.stderr)
                return result
            
            # If no exact match, try approximate match
            print(f"[DEBUG] No exact match for {drug_name}, trying approximate match", file=sys.stderr)
            approx_url = f"{self.rxnorm_base_url}/approximateTerm.json"
            approx_params = {"term": drug_name, "maxEntries": 1}
            
            print(f"[DEBUG] RxNorm approx match request: {approx_url} with params {approx_params}", file=sys.stderr)
            approx_response = requests.get(approx_url, params=approx_params, timeout=10)
            approx_response.raise_for_status()
            approx_data = approx_response.json()
            print(f"[DEBUG] RxNorm approx match response: {approx_data}", file=sys.stderr)
            
            if (approx_data.get("approximateGroup") and 
                approx_data["approximateGroup"].get("candidate") and 
                len(approx_data["approximateGroup"]["candidate"]) > 0):
                
                candidate = approx_data["approximateGroup"]["candidate"][0]
                result = {
                    "rxcui": candidate.get("rxcui"),
                    "name": candidate.get("name", drug_name),
                    "original_name": drug_name,
                    "normalized_name": candidate.get("name", drug_name),
                    "source": "RxNorm",
                    "score": candidate.get("score"),
                    "rank": candidate.get("rank")
                }
                print(f"[DEBUG] Approximate match found for {drug_name}: {result}", file=sys.stderr)
                return result
            
            print(f"[DEBUG] No match found for {drug_name}", file=sys.stderr)
            return None
            
        except Exception as e:
            print(f"[DEBUG] Error normalizing drug name {drug_name}: {str(e)}", file=sys.stderr)
            return None
    
    def get_drug_interactions_rxnorm(self, rxcui_list: List[str]) -> List[Dict]:
        """
        DEPRECATED: RxNorm interaction API endpoints are no longer available.
        
        This method is retained for reference only and will always return an empty list.
        
        Historical Note:
        Older NIH documentation referenced /interaction/interaction.json and /interaction/list.json
        endpoints for retrieving drug interactions. These endpoints have been deprecated and are
        no longer functional. The NLM has not provided replacement endpoints for this functionality.
        
        Current Solution:
        Drug interaction data is now retrieved from:
        1. FDA drug labels via OpenFDA API (contraindications, warnings, precautions)
        2. Web search results via SerpAPI for current interaction information
        3. Future: DrugBank API (requires paid subscription)
        
        Args:
            rxcui_list: List of RxCUI identifiers (DEPRECATED - no longer used)
        
        Returns:
            Empty list (RxNorm interaction API is not available)
        """
        import sys
        # Log that this endpoint is deprecated
        print(f"[DEBUG] get_drug_interactions_rxnorm called - this method is deprecated", file=sys.stderr)
        print(f"[DEBUG] RxNorm interaction API endpoints are no longer available", file=sys.stderr)
        print(f"[DEBUG] Use FDA drug labels and web search for interaction data instead", file=sys.stderr)
        
        return []  # Return empty list since the API is deprecated
    
    def get_drug_interactions_drugbank(self, drug_names: List[str]) -> List[Dict]:
        """
        Get drug interactions from DrugBank database (RAG approach).
        
        Uses local DrugBank database for fast, comprehensive interaction lookup.
        Includes fuzzy matching fallback for brand vs generic name mismatches.
        
        Args:
            drug_names: List of normalized drug names
        
        Returns:
            List of interaction dictionaries
        """
        import sys
        
        if not self.drugbank_db:
            print(f"[WARNING] DrugBank database not initialized", file=sys.stderr)
            return []
        
        interactions = []
        
        try:
            # Look up each drug in the database
            drug_ids = []
            for drug_name in drug_names:
                # Try exact match first, then fuzzy match as fallback
                drug = self.drugbank_db.get_drug_by_name_fuzzy(drug_name)
                if drug:
                    drug_ids.append(drug["id"])
                    print(f"[DEBUG] Found DrugBank entry for {drug_name}: {drug['id']} (name in DB: {drug['name']})", file=sys.stderr)
                else:
                    print(f"[DEBUG] No DrugBank entry found for {drug_name} (tried exact and partial match)", file=sys.stderr)
            
            if not drug_ids:
                print(f"[WARNING] No drugs found in DrugBank database", file=sys.stderr)
                return []
            
            # Get interaction matrix for all drug combinations
            db_interactions = self.drugbank_db.get_interaction_matrix(drug_ids)
            
            for interaction in db_interactions:
                interactions.append({
                    "drug1_id": interaction["drug_id"],
                    "drug2_id": interaction["interacting_drug_id"],
                    "drug2_name": interaction["interacting_drug_name"],
                    "description": interaction["description"],
                    "source": "DrugBank",
                    "confidence": "high"
                })
            
            print(f"[DEBUG] Found {len(interactions)} interactions from DrugBank", file=sys.stderr)
            return interactions
            
        except Exception as e:
            print(f"[ERROR] Error getting DrugBank interactions: {str(e)}", file=sys.stderr)
            return []
    
    def get_drug_details_drugbank(self, drug_name: str) -> Optional[Dict]:
        """
        Get detailed drug information from DrugBank database.
        
        Args:
            drug_name: Name of the drug
        
        Returns:
            Dictionary with drug details or None
        """
        import sys
        
        if not self.drugbank_db:
            return None
        
        try:
            drug = self.drugbank_db.get_drug_by_name(drug_name)
            if drug:
                print(f"[DEBUG] Retrieved DrugBank details for {drug_name}", file=sys.stderr)
                return drug
            return None
            
        except Exception as e:
            print(f"[ERROR] Error getting DrugBank details for {drug_name}: {str(e)}", file=sys.stderr)
            return None
    
    def get_food_interactions_drugbank(self, drug_name: str) -> List[str]:
        """
        Get food interactions from DrugBank database.
        Uses fuzzy matching to handle brand vs generic name differences.
        
        Args:
            drug_name: Name of the drug
        
        Returns:
            List of food interaction descriptions
        """
        import sys
        
        if not self.drugbank_db:
            return []
        
        try:
            # Try exact match first, then fuzzy match as fallback
            drug = self.drugbank_db.get_drug_by_name_fuzzy(drug_name)
            if not drug:
                print(f"[DEBUG] No DrugBank entry found for food interactions: {drug_name}", file=sys.stderr)
                return []
            
            interactions = self.drugbank_db.get_food_interactions(drug["id"])
            if interactions:
                print(f"[DEBUG] Found {len(interactions)} food interactions for {drug_name} (matched to: {drug['name']})", file=sys.stderr)
            return interactions
            
        except Exception as e:
            print(f"[ERROR] Error getting food interactions for {drug_name}: {str(e)}", file=sys.stderr)
            return []
    
    def search_drugbank(self, search_term: str) -> List[Dict]:
        """
        Search DrugBank database for drugs by name.
        
        Args:
            search_term: Partial drug name
        
        Returns:
            List of matching drug dictionaries
        """
        import sys
        
        if not self.drugbank_db:
            return []
        
        try:
            results = self.drugbank_db.search_drugs(search_term)
            print(f"[DEBUG] DrugBank search for '{search_term}' returned {len(results)} results", file=sys.stderr)
            return results
            
        except Exception as e:
            print(f"[ERROR] Error searching DrugBank: {str(e)}", file=sys.stderr)
            return []
    
    def get_fda_drug_info(self, drug_name: str) -> Optional[Dict]:
        """
        Get drug information from FDA API including contraindications and warnings.
        
        Args:
            drug_name: Name of the drug
        
        Returns:
            Dictionary with FDA drug information or None
        """
        import sys
        try:
            # FDA Drug Labeling API
            url = f"{self.fda_base_url}/drug/label.json"
            params = {
                "search": f"openfda.brand_name:{drug_name}",
                "limit": 1
            }
            
            print(f"[DEBUG] Querying FDA for drug info: {drug_name}", file=sys.stderr)
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
                
                # Extract key sections that contain interaction/contraindication info
                contraindications = result.get("contraindications_and_usage", [])
                warnings = result.get("warnings", [])
                precautions = result.get("precautions", [])
                drug_interactions_section = result.get("drug_interactions", [])
                
                fda_info = {
                    "drug_name": drug_name,
                    "brand_name": brand_name,
                    "generic_name": generic_name,
                    "warnings": warnings,
                    "contraindications": contraindications,
                    "precautions": precautions,
                    "drug_interactions": drug_interactions_section,
                    "source": "FDA"
                }
                
                print(f"[DEBUG] FDA info retrieved for {drug_name}: has warnings={len(warnings)}, interactions={len(drug_interactions_section)}", file=sys.stderr)
                return fda_info
            
            print(f"[DEBUG] No FDA results found for {drug_name}", file=sys.stderr)
            return None
            
        except Exception as e:
            print(f"[DEBUG] Error getting FDA info for {drug_name}: {str(e)}", file=sys.stderr)
            return None
    
    def search_drug_websites(self, drug_name: str) -> List[Dict]:
        """
        Perform web search for drug information using SerpAPI (RAG approach).
        
        Args:
            drug_name: Name of the drug
        
        Returns:
            List of search results with drug information
        """
        if not Config.SERPAPI_KEY:
            # Fallback if SerpAPI key is not configured
            return []
        
        try:
            from serpapi import GoogleSearch
            
            params = {
                "q": f"{drug_name} medication side effects interactions",
                "api_key": Config.SERPAPI_KEY,
                "num": 3,  # Get top 3 results
                "engine": "google"
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            web_results = []
            
            # Extract organic search results
            if "organic_results" in results:
                for result in results["organic_results"][:3]:  # Limit to top 3
                    web_results.append({
                        "drug_name": drug_name,
                        "source": "web_search",
                        "title": result.get("title", ""),
                        "snippet": result.get("snippet", ""),
                        "url": result.get("link", ""),
                        "confidence": "medium"
                    })
            
            return web_results
            
        except ImportError:
            print(f"SerpAPI library not available. Install: pip install google-search-results")
            return []
        except Exception as e:
            print(f"Error searching drug websites for {drug_name}: {str(e)}")
            return []


def normalize_medications(medications: List[str], api_client: DrugAPIClient) -> List[Dict]:
    """
    Normalize a list of medication names using RxNorm.
    
    Args:
        medications: List of medication names (brand or common names)
        api_client: DrugAPIClient instance
    
    Returns:
        List of normalized medication dictionaries
    """
    import sys
    normalized = []
    
    for med in medications:
        print(f"[DEBUG] Normalizing medication: {med}", file=sys.stderr)
        normalized_med = api_client.normalize_drug_name_rxnorm(med)
        print(f"[DEBUG] Result for {med}: {normalized_med}", file=sys.stderr)
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

