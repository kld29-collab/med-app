"""
Agent 2: Retrieval/Database Agent (Deterministic Layer)
Executes queries against medication databases and returns structured interaction data.
NO LLM involvement - pure deterministic data retrieval.
"""
from typing import List, Dict, Optional
from utils.drug_apis import DrugAPIClient, normalize_medications


class RetrievalAgent:
    """Retrieves medication interaction data from external databases."""
    
    def __init__(self):
        """Initialize the retrieval agent with API clients."""
        self.api_client = DrugAPIClient()
    
    def retrieve_interactions(self, query_plan: Dict) -> Dict:
        """
        Execute retrieval plan and return structured interaction data.
        
        Args:
            query_plan: Structured query from Query Interpreter Agent
                {
                    "medications": [...],
                    "foods": [...],
                    "supplements": [...],
                    "query_type": "...",
                    "user_context": {...}
                }
        
        Returns:
            Dictionary with structured interaction results
        """
        medications = query_plan.get("medications", [])
        foods = query_plan.get("foods", [])
        supplements = query_plan.get("supplements", [])
        
        results = {
            "normalized_medications": [],
            "drug_interactions": [],
            "food_interactions": [],
            "supplement_interactions": [],
            "fda_info": [],
            "web_sources": [],
            "citations": [],
            "metadata": {
                "query_type": query_plan.get("query_type", "interaction_check"),
                "sources_queried": []
            }
        }
        
        # Step 1: Normalize medication names using RxNorm
        if medications:
            normalized = normalize_medications(medications, self.api_client)
            results["normalized_medications"] = normalized
            results["metadata"]["sources_queried"].append("RxNorm")
            
            # Extract normalized names and RxCUIs for further queries
            # Filter out empty strings and ensure we have valid medication names
            normalized_names = [
                med.get("normalized_name") or med.get("original_name")
                for med in normalized
                if (med.get("normalized_name") or med.get("original_name"))
            ]
            
            # Extract RxCUIs for interaction checking
            rxcui_list = [
                str(med.get("rxcui"))
                for med in normalized
                if med.get("rxcui")
            ]
            
            # Step 2: Get drug-drug interactions from RxNorm (public, no auth required)
            if len(rxcui_list) > 1:
                interactions = self.api_client.get_drug_interactions_rxnorm(rxcui_list)
                results["drug_interactions"].extend(interactions)
                results["metadata"]["sources_queried"].append("RxNorm Interactions")
            
            # Step 2b: Optionally get additional interactions from DrugBank (if credentials available)
            if len(normalized_names) > 1:
                drugbank_interactions = self.api_client.get_drug_interactions_drugbank(normalized_names)
                if drugbank_interactions:
                    results["drug_interactions"].extend(drugbank_interactions)
                    results["metadata"]["sources_queried"].append("DrugBank")
            
            # Step 3: Get FDA information for each medication
            fda_queried = False
            for med_name in medications:
                fda_info = self.api_client.get_fda_drug_info(med_name)
                if fda_info:
                    results["fda_info"].append(fda_info)
                    results["citations"].append({
                        "source": "FDA",
                        "drug": med_name,
                        "url": f"https://www.fda.gov/drugs"
                    })
                    fda_queried = True
            
            if fda_queried:
                results["metadata"]["sources_queried"].append("FDA")
            
            # Step 4: Web RAG search for additional context
            web_queried = False
            for med_name in medications:
                web_results = self.api_client.search_drug_websites(med_name)
                if web_results:
                    results["web_sources"].extend(web_results)
                    web_queried = True
            
            if web_queried:
                results["metadata"]["sources_queried"].append("Web")
        
        # Step 5: Handle food interactions
        if foods:
            # Food interactions would be queried similarly
            # This is a placeholder - actual implementation depends on available APIs
            for food in foods:
                # Only add if food name is valid (not None or empty)
                if food and food.strip():
                    results["food_interactions"].append({
                        "food": food.strip(),
                        "interactions": [],
                        "source": "database",
                        "note": "Food interaction data would be retrieved here"
                    })
        
        # Step 6: Handle supplement interactions
        if supplements:
            # Supplement interactions would be queried similarly
            for supplement in supplements:
                # Only add if supplement name is valid (not None or empty)
                if supplement and supplement.strip():
                    results["supplement_interactions"].append({
                        "supplement": supplement.strip(),
                        "interactions": [],
                        "source": "database",
                        "note": "Supplement interaction data would be retrieved here"
                    })
        
        # Build interaction table
        interaction_table = self._build_interaction_table(results)
        results["interaction_table"] = interaction_table
        
        return results
    
    def _build_interaction_table(self, results: Dict) -> List[Dict]:
        """
        Build a structured interaction table from retrieved data.
        
        Args:
            results: Results dictionary from retrieve_interactions
        
        Returns:
            List of interaction records
        """
        table = []
        
        # Add drug-drug interactions
        for interaction in results.get("drug_interactions", []):
            drug1 = interaction.get("drug1")
            drug2 = interaction.get("drug2")
            # Only add if both drugs have valid names (not empty or None)
            if drug1 and drug2:
                table.append({
                    "type": "drug-drug",
                    "item1": drug1,
                    "item2": drug2,
                    "severity": interaction.get("severity", "unknown"),
                    "description": interaction.get("description", ""),
                    "source": interaction.get("source", ""),
                    "confidence": interaction.get("confidence", "medium")
                })
        
        # Add food interactions
        for interaction in results.get("food_interactions", []):
            food_name = interaction.get("food")
            # Validate both medication and food names before adding
            if food_name:  # Only proceed if we have a valid food name
                for med in results.get("normalized_medications", []):
                    med_name = med.get("normalized_name") or med.get("original_name")
                    if med_name:  # Only add if we have a valid medication name
                        table.append({
                            "type": "drug-food",
                            "item1": med_name,
                            "item2": food_name,
                            "severity": "unknown",
                            "description": interaction.get("note", ""),
                            "source": interaction.get("source", ""),
                            "confidence": "low"
                        })
        
        # Add supplement interactions
        for interaction in results.get("supplement_interactions", []):
            supplement_name = interaction.get("supplement")
            # Validate both medication and supplement names before adding
            if supplement_name:  # Only proceed if we have a valid supplement name
                for med in results.get("normalized_medications", []):
                    med_name = med.get("normalized_name") or med.get("original_name")
                    if med_name:  # Only add if we have a valid medication name
                        table.append({
                            "type": "drug-supplement",
                            "item1": med_name,
                            "item2": supplement_name,
                            "severity": "unknown",
                            "description": interaction.get("note", ""),
                            "source": interaction.get("source", ""),
                            "confidence": "low"
                        })
        
        return table

