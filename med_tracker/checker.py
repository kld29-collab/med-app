"""
Interaction Checker

Core logic for analyzing medication, supplement, and food interactions.
Combines data from multiple sources and structures the results.
"""

from typing import Dict, List
from .api_client import MedicationAPIClient


class InteractionChecker:
    """Analyzes medication, supplement, and food interactions."""
    
    # Known food-drug interactions (educational purposes)
    FOOD_DRUG_INTERACTIONS = {
        "grapefruit": [
            {
                "drugs": ["statins", "atorvastatin", "simvastatin", "lovastatin"],
                "interaction": "Grapefruit can increase drug levels in blood",
                "severity": "High",
                "recommendation": "Avoid grapefruit and grapefruit juice"
            },
            {
                "drugs": ["calcium channel blockers", "amlodipine", "nifedipine"],
                "interaction": "May cause excessive blood pressure lowering",
                "severity": "Moderate",
                "recommendation": "Consult healthcare provider"
            }
        ],
        "alcohol": [
            {
                "drugs": ["acetaminophen", "metformin", "warfarin"],
                "interaction": "Increased risk of liver damage or altered drug effectiveness",
                "severity": "High",
                "recommendation": "Avoid or limit alcohol consumption"
            }
        ],
        "leafy greens": [
            {
                "drugs": ["warfarin", "anticoagulants"],
                "interaction": "Vitamin K in greens can reduce drug effectiveness",
                "severity": "Moderate",
                "recommendation": "Maintain consistent intake"
            }
        ],
        "dairy": [
            {
                "drugs": ["tetracycline", "ciprofloxacin", "fluoroquinolones"],
                "interaction": "Calcium can reduce antibiotic absorption",
                "severity": "Moderate",
                "recommendation": "Take medication 2 hours before or after dairy"
            }
        ],
        "caffeine": [
            {
                "drugs": ["ephedrine", "theophylline", "bronchodilators"],
                "interaction": "May increase stimulant effects and side effects",
                "severity": "Low",
                "recommendation": "Monitor caffeine intake"
            }
        ]
    }
    
    # Known supplement-drug interactions
    SUPPLEMENT_DRUG_INTERACTIONS = {
        "st john's wort": [
            {
                "drugs": ["antidepressants", "birth control", "warfarin", "immunosuppressants"],
                "interaction": "Can reduce effectiveness of many medications",
                "severity": "High",
                "recommendation": "Avoid combining; consult healthcare provider"
            }
        ],
        "vitamin k": [
            {
                "drugs": ["warfarin", "anticoagulants"],
                "interaction": "Can reduce anticoagulant effectiveness",
                "severity": "High",
                "recommendation": "Maintain consistent intake"
            }
        ],
        "iron": [
            {
                "drugs": ["levothyroxine", "thyroid medications"],
                "interaction": "Can reduce thyroid medication absorption",
                "severity": "Moderate",
                "recommendation": "Take 4 hours apart"
            }
        ],
        "calcium": [
            {
                "drugs": ["levothyroxine", "antibiotics", "bisphosphonates"],
                "interaction": "Can reduce drug absorption",
                "severity": "Moderate",
                "recommendation": "Take medications 2-4 hours apart from calcium"
            }
        ]
    }
    
    def __init__(self, api_key: str = None):
        """
        Initialize the interaction checker.
        
        Args:
            api_key: Optional DrugBank API key
        """
        self.api_client = MedicationAPIClient(drugbank_api_key=api_key)
    
    def check_interactions(self, medications: List[str], supplements: List[str] = None, 
                          foods: List[str] = None) -> Dict:
        """
        Check for interactions among medications, supplements, and foods.
        
        Args:
            medications: List of medication names
            supplements: List of supplement names
            foods: List of food items
            
        Returns:
            Structured dictionary with all interaction findings
        """
        supplements = supplements or []
        foods = foods or []
        
        result = {
            "medications": medications,
            "supplements": supplements,
            "foods": foods,
            "drug_drug_interactions": [],
            "drug_food_interactions": [],
            "drug_supplement_interactions": [],
            "summary": {
                "high_severity_count": 0,
                "moderate_severity_count": 0,
                "low_severity_count": 0,
                "total_interactions": 0
            }
        }
        
        # Check drug-drug interactions via API
        if len(medications) > 0:
            api_results = self.api_client.check_multiple_interactions(medications)
            result["drug_drug_interactions"] = api_results.get("potential_interactions", [])
            
            # Also include interactions found for individual drugs
            for med, info in api_results.get("individual_results", {}).items():
                for interaction in info.get("interactions", []):
                    # Check if the interacting drug is in our list
                    interacting_drug_name = interaction["interacting_drug"]
                    already_recorded = any(
                        i.get("drug2", "").lower() in interacting_drug_name.lower() or
                        interacting_drug_name.lower() in i.get("drug2", "").lower()
                        for i in result["drug_drug_interactions"]
                    )
                    
                    if not already_recorded:
                        result["drug_drug_interactions"].append({
                            "drug1": med,
                            "drug2": interacting_drug_name,
                            "severity": interaction["severity"],
                            "description": interaction["description"]
                        })
        
        # Check drug-food interactions
        for food in foods:
            food_lower = food.lower()
            if food_lower in self.FOOD_DRUG_INTERACTIONS:
                for interaction_data in self.FOOD_DRUG_INTERACTIONS[food_lower]:
                    for med in medications:
                        if any(drug.lower() in med.lower() or med.lower() in drug.lower() 
                              for drug in interaction_data["drugs"]):
                            result["drug_food_interactions"].append({
                                "medication": med,
                                "food": food,
                                "interaction": interaction_data["interaction"],
                                "severity": interaction_data["severity"],
                                "recommendation": interaction_data["recommendation"]
                            })
        
        # Check drug-supplement interactions
        for supplement in supplements:
            supp_lower = supplement.lower()
            if supp_lower in self.SUPPLEMENT_DRUG_INTERACTIONS:
                for interaction_data in self.SUPPLEMENT_DRUG_INTERACTIONS[supp_lower]:
                    for med in medications:
                        if any(drug.lower() in med.lower() or med.lower() in drug.lower()
                              for drug in interaction_data["drugs"]):
                            result["drug_supplement_interactions"].append({
                                "medication": med,
                                "supplement": supplement,
                                "interaction": interaction_data["interaction"],
                                "severity": interaction_data["severity"],
                                "recommendation": interaction_data["recommendation"]
                            })
        
        # Calculate summary statistics
        all_interactions = (
            result["drug_drug_interactions"] + 
            result["drug_food_interactions"] + 
            result["drug_supplement_interactions"]
        )
        
        for interaction in all_interactions:
            severity = interaction.get("severity", "").lower()
            if "high" in severity or "major" in severity:
                result["summary"]["high_severity_count"] += 1
            elif "moderate" in severity:
                result["summary"]["moderate_severity_count"] += 1
            else:
                result["summary"]["low_severity_count"] += 1
        
        result["summary"]["total_interactions"] = len(all_interactions)
        
        return result
