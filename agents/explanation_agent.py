"""
Agent 3: Explanation Agent
Translates technical interaction data into plain-language explanations.

Data sources summarized in explanations:
- RxNorm: Drug name normalization only (interaction API is deprecated)
- FDA Drug Labels (OpenFDA): Contraindications, warnings, precautions
- Web Search (SerpAPI): Current interaction information from clinical sources
- DrugBank (optional): Professional drug interaction database (paid)
"""
import json
import sys
from typing import Dict, List
from config import Config
from utils.openai_client import initialize_openai_client, cleanup_environment

# Cleanup environment on module load
cleanup_environment()


class ExplanationAgent:
    """Generates user-friendly explanations from technical interaction data."""
    
    def __init__(self):
        """Initialize the explanation agent with OpenAI client."""
        print(f"[DEBUG] Initializing ExplanationAgent...", file=sys.stderr)
        self.client = initialize_openai_client("ExplanationAgent")
        self.model = Config.OPENAI_MODEL
    
    def generate_explanation(self, interaction_data: Dict, user_context: Dict = None) -> Dict:
        """
        Generate plain-language explanation from interaction data.
        
        Args:
            interaction_data: Structured interaction data from Retrieval Agent
            user_context: Optional user context (age, weight, height, conditions)
        
        Returns:
            Dictionary with user-facing explanation and metadata
        """
        if user_context is None:
            user_context = {}
        
        # Get interaction data - retrieval agent returns "drug_interactions" not "interaction_table"
        interaction_table = interaction_data.get("drug_interactions", interaction_data.get("interaction_table", []))
        normalized_medications = interaction_data.get("normalized_medications", [])
        citations = interaction_data.get("citations", [])
        web_sources = interaction_data.get("web_sources", [])
        fda_info = interaction_data.get("fda_info", [])
        food_interactions = interaction_data.get("food_interactions", [])
        query_focus = interaction_data.get("metadata", {}).get("query_focus", "general")
        
        # DEBUG: Log what we received
        print(f"[DEBUG EXPLANATION] Query focus: {query_focus}", file=sys.stderr)
        print(f"[DEBUG EXPLANATION] Food interactions count: {len(food_interactions)}", file=sys.stderr)
        print(f"[DEBUG EXPLANATION] Drug interactions count: {len(interaction_table)}", file=sys.stderr)
        if food_interactions:
            print(f"[DEBUG EXPLANATION] First food interaction: {food_interactions[0]}", file=sys.stderr)
        
        system_prompt = """You are a medical information translator. Your ONLY job is to explain 
        the medication interaction data provided to you. Nothing more.

        CRITICAL RULES (FOLLOW THESE EXACTLY):
        1. ONLY explain the data provided - do not make up information
        2. If food interactions data is provided AND query_focus="food": MUST explain the food interactions
        3. Do NOT say "no interactions found" or "specific details were not provided" if you have interaction text/data
        4. If the user asked about food (query_focus="food"): explain EVERY food interaction in the list
        5. Use simple, clear language - avoid medical jargon
        6. Always recommend consulting a healthcare provider
        7. Extract severity from the description text:
           - Look for keywords like "bleeding risk", "increase INR", "serious", "life-threatening" = HIGH
           - Look for keywords like "interfere with", "reduce efficacy", "increase levels" = MODERATE
           - Look for keywords like "may affect", "possible" = MILD
           - If severity is unclear, use "unknown"
        8. Each food interaction description contains the details - USE THEM in the explanation
        
        RESPONSE FORMAT: Return ONLY valid JSON in this exact structure:
        {
            "summary": "Brief 2-3 sentence summary of findings",
            "interactions": [
                {
                    "items": ["food item name"],
                    "type": "food-drug",
                    "explanation": "What the interaction is based on the provided description",
                    "severity": "high/moderate/mild/unknown",
                    "recommendation": "What to do about this based on the provided description"
                }
            ],
            "uncertainties": ["any uncertain or low-confidence information"],
            "disclaimer": "Medical disclaimer",
            "recommendation": "Overall recommendation"
        }
        
        DO NOT DEVIATE FROM THIS FORMAT. Every description already contains the interaction details."""
        
        # Build food interactions display with better formatting
        food_interactions_display = ""
        for i, interaction in enumerate(food_interactions, 1):
            # Handle both string and dict formats
            if isinstance(interaction, dict):
                food_name = interaction.get("food", "Unknown food")
                if isinstance(food_name, str):
                    description = food_name
                else:
                    description = str(food_name)
            else:
                description = str(interaction)
            food_interactions_display += f"\n{i}. {description}"
        
        user_prompt = f"""INTERACTION DATA TO EXPLAIN:

User's Query Focus: {query_focus}

Medications: {json.dumps(normalized_medications, indent=2)}

FOOD/BEVERAGE INTERACTIONS ({len(food_interactions)} items found):{food_interactions_display}

DRUG-DRUG INTERACTIONS ({len(interaction_table)} items found):
{json.dumps(interaction_table, indent=2) if interaction_table else "(empty)"}

FDA Information:
{json.dumps(fda_info, indent=2) if fda_info else "(none)"}

Web Search Results:
{json.dumps(web_sources[:2], indent=2) if web_sources else "(none)"}

YOUR TASK:
1. Query focus is: {query_focus}
2. Focus on: {"FOOD/BEVERAGE interactions ONLY" if query_focus == "food" else "DRUG-DRUG interactions ONLY" if query_focus == "drug_drug" else "all interactions"}
3. You have {len(food_interactions)} food interactions provided above
4. You have {len(interaction_table)} drug interactions to include if relevant
5. For each food interaction, extract:
   - Food/beverage name
   - What the description says about the interaction
   - Severity based on keywords (bleeding risk = HIGH, interfere with metabolism = MODERATE, etc)
   - Recommendation from the description

IMPORTANT: The interaction descriptions already contain all the details you need. Do NOT say "specific details were not provided" - they are provided in the descriptions above. Create one interaction object for each of the {len(food_interactions)} food interactions listed."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3  # Slightly higher for more natural language, but still controlled
            )
            
            explanation = json.loads(response.choices[0].message.content)
            
            # Add metadata with source details for display
            sources_list = []
            
            # Build sources list from available data
            if interaction_table:
                sources_list.append({
                    "name": "DrugBank",
                    "type": "drug-interactions",
                    "count": len(interaction_table),
                    "description": "Local drug interaction database"
                })
            
            if fda_info:
                sources_list.append({
                    "name": "FDA",
                    "type": "drug-labels",
                    "count": len(fda_info),
                    "description": "Official FDA drug labeling information"
                })
            
            if web_sources:
                sources_list.append({
                    "name": "Web Search",
                    "type": "web-results",
                    "count": len(web_sources),
                    "description": "Clinical and medical websites"
                })
            
            if citations:
                sources_list.append({
                    "name": "Citations",
                    "type": "citations",
                    "count": len(citations),
                    "description": "Referenced sources"
                })
            
            explanation["metadata"] = {
                "sources_used": interaction_data.get("metadata", {}).get("sources_queried", []),
                "citation_count": len(citations),
                "interaction_count": len(interaction_table),
                "sources": sources_list
            }
            
            # Include raw source data for expandable panel
            explanation["raw_sources"] = {
                "drugbank": interaction_table if interaction_table else [],
                "food": food_interactions if food_interactions else [],
                "fda": fda_info if fda_info else [],
                "web": web_sources if web_sources else [],
                "citations": citations if citations else []
            }
            
            # Ensure disclaimer is present
            if "disclaimer" not in explanation or not explanation["disclaimer"]:
                explanation["disclaimer"] = (
                    "This information is for educational purposes only and does not constitute "
                    "medical advice. Always consult with a qualified healthcare provider before "
                    "making decisions about your medications."
                )
            
            return explanation
            
        except json.JSONDecodeError as e:
            # Fallback explanation if JSON parsing fails
            return {
                "summary": "An error occurred while generating the explanation. Please consult your healthcare provider.",
                "interactions": [],
                "uncertainties": ["Error parsing explanation response"],
                "disclaimer": (
                    "This information is for educational purposes only and does not constitute "
                    "medical advice. Always consult with a qualified healthcare provider."
                ),
                "recommendation": "Please consult your healthcare provider for personalized medical advice.",
                "error": f"Failed to parse explanation: {str(e)}"
            }
        except Exception as e:
            return {
                "summary": "An error occurred while processing your query. Please try again or consult your healthcare provider.",
                "interactions": [],
                "uncertainties": [f"Error: {str(e)}"],
                "disclaimer": (
                    "This information is for educational purposes only and does not constitute "
                    "medical advice. Always consult with a qualified healthcare provider."
                ),
                "recommendation": "Please consult your healthcare provider for personalized medical advice.",
                "error": f"Error generating explanation: {str(e)}"
            }
    
    def format_for_display(self, explanation: Dict) -> str:
        """
        Format explanation dictionary into a user-friendly text format.
        
        Args:
            explanation: Explanation dictionary from generate_explanation
        
        Returns:
            Formatted string for display
        """
        lines = []
        
        # Summary
        if explanation.get("summary"):
            lines.append(f"**Summary:**\n{explanation['summary']}\n")
        
        # Interactions
        if explanation.get("interactions"):
            lines.append("**Interactions:**\n")
            for i, interaction in enumerate(explanation["interactions"], 1):
                # Safely join items: filter out None, convert to strings, handle empty lists
                items_list = interaction.get("items", [])
                items_str = " and ".join(
                    str(item) for item in items_list 
                    if item is not None
                ) if items_list else "Unknown items"
                lines.append(f"{i}. **{items_str}** ({interaction.get('type', 'unknown')})")
                lines.append(f"   {interaction.get('explanation', 'No explanation available')}")
                if interaction.get("severity"):
                    lines.append(f"   Severity: {interaction['severity']}")
                if interaction.get("recommendation"):
                    lines.append(f"   Recommendation: {interaction['recommendation']}")
                lines.append("")
        
        # Uncertainties
        if explanation.get("uncertainties"):
            lines.append("**Note:**")
            for uncertainty in explanation["uncertainties"]:
                lines.append(f"- {uncertainty}")
            lines.append("")
        
        # Recommendation
        if explanation.get("recommendation"):
            lines.append(f"**Recommendation:**\n{explanation['recommendation']}\n")
        
        # Disclaimer
        if explanation.get("disclaimer"):
            lines.append(f"**Disclaimer:**\n{explanation['disclaimer']}")
        
        return "\n".join(lines)

