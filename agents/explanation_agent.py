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
        
        # DEBUG: Log received user context
        print(f"[DEBUG EXPLANATION] User context received: {user_context}", file=sys.stderr)
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
        
        system_prompt = """You are a medical information translator. Explain medication interaction data clearly and concisely, considering user health context.

RULES:
1. Only explain provided data - no fabrication
2. Do NOT say "no data" or "details missing" if you have text to work with
3. Use simple language, avoid jargon
4. Severity: HIGH (bleeding, serious risk), MODERATE (interfere/reduce), MILD (may affect)
5. Always recommend consulting a healthcare provider
6. CRITICAL: When user has health conditions mentioned (e.g., migraine, diabetes, hypertension), explicitly note ANY relevant medication concerns or contraindications related to those conditions
7. Consider the user's sex - some medications have different risks for male vs female (e.g., hormonal birth control risks with migraines with aura)

RESPOND WITH ONLY THIS JSON FORMAT (fill in actual content):
{"summary":"2-3 sentences","interactions":[{"items":["drug1","drug2"],"type":"drug-drug","explanation":"plain text","severity":"high/moderate/mild/unknown","recommendation":"specific action"}],"uncertainties":[],"disclaimer":"Educational disclaimer text","recommendation":"Specific advice based on data"}"""
        
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
        
        # Build user context info for prompt
        user_context_display = ""
        if user_context:
            context_items = []
            if user_context.get('age'):
                context_items.append(f"Age: {user_context['age']}")
            if user_context.get('sex'):
                context_items.append(f"Sex: {user_context['sex']}")
            if user_context.get('weight'):
                context_items.append(f"Weight: {user_context['weight']} lbs")
            if user_context.get('conditions'):
                conditions = user_context['conditions']
                if isinstance(conditions, list) and conditions:
                    context_items.append(f"Health conditions: {', '.join(conditions)}")
            if context_items:
                user_context_display = "\n\nUser context: " + "; ".join(context_items)
                print(f"[DEBUG EXPLANATION] Built user context display: {user_context_display}", file=sys.stderr)
        
        # Build FDA info display (concise format)
        fda_info_display = ""
        if fda_info:
            fda_items = []
            for item in fda_info:
                drug_name = item.get('drug_name', 'Unknown')
                warnings = item.get('warnings', [])
                precautions = item.get('precautions', [])
                contraindications = item.get('contraindications', [])
                drug_interactions = item.get('drug_interactions', [])
                
                # Include warnings if available
                if warnings:
                    # Get first 150 chars of first warning
                    warning_text = warnings[0][:150] if warnings[0] else ""
                    if warning_text:
                        fda_items.append(f"{drug_name}: {warning_text}...")
                
                # Include precautions if available
                if precautions:
                    # Get first 150 chars of precautions
                    precaution_text = precautions[0][:150] if precautions[0] else ""
                    if precaution_text:
                        fda_items.append(f"{drug_name} precautions: {precaution_text}...")
                
                # Include drug interactions from FDA
                if drug_interactions:
                    for interaction in drug_interactions[:1]:  # Only include first
                        interaction_text = interaction[:200] if interaction else ""
                        if interaction_text:
                            fda_items.append(f"{drug_name} interactions: {interaction_text}...")
            
            if fda_items:
                fda_info_display = "\n\nFDA Drug Information:\n" + "\n".join(fda_items)
        
        user_prompt = f"""Medications: {', '.join(m.get('name', m.get('original_name', '')) for m in normalized_medications)}
Query focus: {query_focus}{user_context_display}

Food interactions ({len(food_interactions)}): {food_interactions_display if food_interactions_display else '(none)'}

Drug interactions ({len(interaction_table)}): {json.dumps(interaction_table[:3], indent=0) if interaction_table else '(empty - check FDA data below)'}

{fda_info_display}

Web results: {json.dumps(web_sources[:1], indent=0) if web_sources else '(none)'}

{"Use web search results for additional drug interaction details" if len(interaction_table) == 0 and len(web_sources) > 0 else ""}

IMPORTANT: Include ALL drug interactions mentioned in the data above, including those from FDA sources.
Consider the user context (conditions, age, sex) when explaining interactions and providing recommendations.

Explain all drug interactions based on this data."""
        
        print(f"[DEBUG EXPLANATION] User prompt being sent to model:\n{user_prompt}", file=sys.stderr)
        
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
            
            # Clean up placeholder text that might have been returned
            recommendation = explanation.get("recommendation", "").strip()
            placeholder_recommendations = ["Overall advice", "Consult healthcare provider", "Specific advice based on data"]
            if not recommendation or recommendation in placeholder_recommendations or len(recommendation) < 10:
                explanation["recommendation"] = "Consult your healthcare provider before making any medication changes."
            
            disclaimer = explanation.get("disclaimer", "").strip()
            placeholder_disclaimers = ["Medical disclaimer", "Educational disclaimer text", "Educational disclaimer", "Disclaimer text"]
            if not disclaimer or disclaimer in placeholder_disclaimers or len(disclaimer) < 15:
                explanation["disclaimer"] = (
                    "This information is for educational purposes only and does not constitute "
                    "medical advice. Always consult with a qualified healthcare provider before "
                    "making decisions about your medications."
                )
            
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

