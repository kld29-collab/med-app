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
        self.rxnorm_base_url = Config.RXNORM_BASE_URL
        self.drugbank_username = Config.DRUGBANK_USERNAME
        self.drugbank_password = Config.DRUGBANK_PASSWORD
        self.fda_base_url = Config.FDA_API_BASE_URL
    
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
        Get drug interactions using RxNorm public interaction API (no authentication required).
        NOTE: RxNorm's interaction API has limited coverage. This serves as a supplementary source.
        
        Args:
            rxcui_list: List of RxCUI identifiers
        
        Returns:
            List of interaction dictionaries (may be empty)
        """
        import sys
        interactions = []
        
        try:
            # RxNorm's interaction API is unreliable and has limited data
            # We try it, but don't fail if it returns 404
            for i in range(len(rxcui_list)):
                for j in range(i + 1, len(rxcui_list)):
                    rxcui1 = rxcui_list[i]
                    rxcui2 = rxcui_list[j]
                    
                    # Try different endpoint formats
                    endpoints = [
                        f"{self.rxnorm_base_url}/interaction/list.json",
                        f"{self.rxnorm_base_url}/interaction/listJson.json"
                    ]
                    
                    for url in endpoints:
                        params = {"rxcuis": f"{rxcui1}+{rxcui2}"}
                        
                        print(f"[DEBUG] RxNorm interaction request: {url} with params {params}", file=sys.stderr)
                        try:
                            response = requests.get(url, params=params, timeout=10)
                            
                            if response.status_code == 404:
                                print(f"[DEBUG] RxNorm endpoint {url} returned 404 - no data for this combination", file=sys.stderr)
                                continue
                            
                            response.raise_for_status()
                            data = response.json()
                            print(f"[DEBUG] RxNorm response: {data}", file=sys.stderr)
                            
                            # Parse the interaction response if it exists
                            if data.get("fullInteractionTypeGroup"):
                                for group in data["fullInteractionTypeGroup"]:
                                    if group.get("fullInteractionType"):
                                        for interaction_type in group["fullInteractionType"]:
                                            if interaction_type.get("interactionPair"):
                                                for pair in interaction_type["interactionPair"]:
                                                    interaction_concept = pair.get("interactionConcept", [{}])
                                                    description = pair.get("description", "No description available")
                                                    severity = pair.get("severity", "unknown")
                                                    
                                                    # Extract drug names from the interaction concepts
                                                    drugs = [concept.get("minConceptItem", {}).get("name", "Unknown") 
                                                            for concept in interaction_concept if concept.get("minConceptItem")]
                                                    
                                                    if len(drugs) >= 2:
                                                        interaction_obj = {
                                                            "drug1": drugs[0],
                                                            "drug2": drugs[1],
                                                            "severity": severity,
                                                            "description": description,
                                                            "source": "RxNorm",
                                                            "confidence": "high"
                                                        }
                                                        print(f"[DEBUG] Found interaction: {interaction_obj}", file=sys.stderr)
                                                        interactions.append(interaction_obj)
                                break  # Found working endpoint
                                
                        except requests.exceptions.RequestException as e:
                            print(f"[DEBUG] RxNorm request error for {rxcui1}+{rxcui2}: {str(e)}", file=sys.stderr)
                            continue
            
            print(f"[DEBUG] RxNorm total interactions found: {len(interactions)}", file=sys.stderr)
            return interactions
            
        except Exception as e:
            print(f"[DEBUG] Error in get_drug_interactions_rxnorm: {str(e)}", file=sys.stderr)
            return []
    
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

