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
        # Use GPT-3.5-turbo for explanations: 3.5x faster, 10x cheaper
        # Still produces high-quality JSON explanations without rate limiting issues
        self.model = "gpt-3.5-turbo"
    
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
        
        system_prompt = """You are a medical information translator. Explain medication interaction data clearly and concisely.

RULES:
1. Only explain provided data - no fabrication
2. Do NOT say "no data" or "details missing" if you have text to work with
3. Use simple language, avoid jargon
4. Severity: HIGH (bleeding, serious risk), MODERATE (interfere/reduce), MILD (may affect)
5. Always recommend consulting a healthcare provider

RESPOND WITH ONLY THIS JSON FORMAT:
{"summary":"2-3 sentences","interactions":[{"items":["drug1","drug2"],"type":"drug-drug","explanation":"plain text","severity":"high/moderate/mild/unknown","recommendation":"action"}],"uncertainties":[],"disclaimer":"Medical disclaimer","recommendation":"Overall advice"}"""
        
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
        
        user_prompt = f"""Medications: {', '.join(m.get('name', m.get('original_name', '')) for m in normalized_medications)}
Query focus: {query_focus}

Food interactions ({len(food_interactions)}): {food_interactions_display if food_interactions_display else '(none)'}

Drug interactions ({len(interaction_table)}): {json.dumps(interaction_table[:2], indent=0) if interaction_table else '(empty - use web search below)'}

Web results: {json.dumps(web_sources[:1], indent=0) if web_sources else '(none)'}

{"Use web search results for drug interaction details" if len(interaction_table) == 0 and len(web_sources) > 0 else ""}

Explain interactions based on this data."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,  # Lower temperature for faster, more deterministic responses
                max_tokens=1000  # Limit token generation to reduce latency
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

