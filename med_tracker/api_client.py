"""
Medication Database API Client

Interfaces with external medication databases:
- RxNorm (NIH NLM API)
- OpenFDA Drug API
- DrugBank (requires API key)
"""

import requests
from typing import Dict, List, Optional
import time


class MedicationAPIClient:
    """Client for querying medication databases."""
    
    # Public API endpoints
    RXNORM_BASE_URL = "https://rxnav.nlm.nih.gov/REST"
    FDA_BASE_URL = "https://api.fda.gov/drug"
    
    def __init__(self, drugbank_api_key: Optional[str] = None):
        """
        Initialize the API client.
        
        Args:
            drugbank_api_key: Optional DrugBank API key for enhanced data
        """
        self.drugbank_api_key = drugbank_api_key
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "MedicationInteractionTracker/0.1.0"
        })
    
    def get_rxcui(self, drug_name: str) -> Optional[str]:
        """
        Get RxCUI (RxNorm Concept Unique Identifier) for a drug name.
        
        Args:
            drug_name: Name of the medication
            
        Returns:
            RxCUI string or None if not found
        """
        try:
            url = f"{self.RXNORM_BASE_URL}/rxcui.json"
            params = {"name": drug_name}
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if "idGroup" in data and "rxnormId" in data["idGroup"]:
                rxcui_list = data["idGroup"]["rxnormId"]
                return rxcui_list[0] if rxcui_list else None
            
            return None
            
        except Exception as e:
            print(f"Error fetching RxCUI for {drug_name}: {e}")
            return None
    
    def get_drug_interactions(self, rxcui: str) -> List[Dict]:
        """
        Get drug interactions for a given RxCUI using RxNorm API.
        
        Args:
            rxcui: RxNorm Concept Unique Identifier
            
        Returns:
            List of interaction dictionaries
        """
        try:
            url = f"{self.RXNORM_BASE_URL}/interaction/interaction.json"
            params = {"rxcui": rxcui}
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            interactions = []
            
            if "interactionTypeGroup" in data:
                for type_group in data["interactionTypeGroup"]:
                    if "interactionType" in type_group:
                        for interaction_type in type_group["interactionType"]:
                            if "interactionPair" in interaction_type:
                                for pair in interaction_type["interactionPair"]:
                                    interactions.append({
                                        "interacting_drug": pair.get("interactionConcept", [{}])[0].get("minConceptItem", {}).get("name", "Unknown"),
                                        "severity": pair.get("severity", "Unknown"),
                                        "description": pair.get("description", "No description available")
                                    })
            
            return interactions
            
        except Exception as e:
            print(f"Error fetching interactions for RxCUI {rxcui}: {e}")
            return []
    
    def search_drug_by_name(self, drug_name: str) -> Dict:
        """
        Search for drug information by name using RxNorm.
        
        Args:
            drug_name: Name of the medication
            
        Returns:
            Dictionary with drug information
        """
        result = {
            "drug_name": drug_name,
            "rxcui": None,
            "found": False,
            "interactions": []
        }
        
        # Get RxCUI
        rxcui = self.get_rxcui(drug_name)
        if rxcui:
            result["rxcui"] = rxcui
            result["found"] = True
            
            # Get interactions
            interactions = self.get_drug_interactions(rxcui)
            result["interactions"] = interactions
        
        return result
    
    def get_fda_adverse_events(self, drug_name: str, limit: int = 5) -> List[Dict]:
        """
        Get FDA adverse event data for a drug.
        
        Args:
            drug_name: Name of the medication
            limit: Maximum number of results
            
        Returns:
            List of adverse event dictionaries
        """
        try:
            url = f"{self.FDA_BASE_URL}/event.json"
            params = {
                "search": f'patient.drug.medicinalproduct:"{drug_name}"',
                "limit": limit
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            events = []
            
            if "results" in data:
                for result in data["results"]:
                    reactions = []
                    if "patient" in result and "reaction" in result["patient"]:
                        reactions = [r.get("reactionmeddrapt", "Unknown") 
                                   for r in result["patient"]["reaction"][:3]]
                    
                    events.append({
                        "reactions": reactions,
                        "serious": result.get("serious", 0)
                    })
            
            return events
            
        except Exception as e:
            # FDA API might have rate limits or the drug might not be found
            print(f"Note: Could not fetch FDA data for {drug_name}: {e}")
            return []
    
    def check_multiple_interactions(self, drug_names: List[str]) -> Dict:
        """
        Check for interactions among multiple drugs.
        
        Args:
            drug_names: List of drug names to check
            
        Returns:
            Dictionary with comprehensive interaction data
        """
        result = {
            "drugs_checked": drug_names,
            "individual_results": {},
            "potential_interactions": []
        }
        
        # Get info for each drug
        for drug_name in drug_names:
            drug_info = self.search_drug_by_name(drug_name)
            result["individual_results"][drug_name] = drug_info
            
            # Check if any of the other drugs appear in this drug's interactions
            for interaction in drug_info["interactions"]:
                interacting_drug = interaction["interacting_drug"].lower()
                for other_drug in drug_names:
                    if other_drug != drug_name and other_drug.lower() in interacting_drug:
                        result["potential_interactions"].append({
                            "drug1": drug_name,
                            "drug2": other_drug,
                            "severity": interaction["severity"],
                            "description": interaction["description"]
                        })
            
            # Small delay to be respectful to public APIs
            time.sleep(0.1)
        
        return result
