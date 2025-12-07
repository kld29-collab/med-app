"""
Agent 3: Explanation Agent
Translates technical interaction data into plain-language explanations.
"""
import json
from openai import OpenAI
from config import Config
from typing import Dict, List


class ExplanationAgent:
    """Generates user-friendly explanations from technical interaction data."""
    
    def __init__(self):
        """Initialize the explanation agent with OpenAI client."""
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured. Please set it in your environment variables.")
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
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
        
        interaction_table = interaction_data.get("interaction_table", [])
        normalized_medications = interaction_data.get("normalized_medications", [])
        citations = interaction_data.get("citations", [])
        
        system_prompt = """You are a medical information translator. Your job is to take technical 
        medication interaction data and explain it in plain, everyday language that non-medical users 
        can understand.

        IMPORTANT RULES:
        1. ONLY use information provided in the interaction data - do not add information not present
        2. Use simple, clear language - avoid medical jargon
        3. If information is uncertain or conflicting, clearly state that
        4. Always recommend consulting a healthcare provider for medical decisions
        5. Include appropriate safety disclaimers
        6. Flag any uncertainties or low-confidence data
        7. Explain WHY an interaction might occur if that information is available

        Structure your response as JSON with these fields:
        {
            "summary": "Brief overall summary (2-3 sentences)",
            "interactions": [
                {
                    "items": ["item1", "item2"],
                    "type": "drug-drug",
                    "explanation": "Plain language explanation",
                    "severity": "high/medium/low/unknown",
                    "recommendation": "What the user should do"
                }
            ],
            "uncertainties": ["List any uncertainties or conflicting information"],
            "disclaimer": "Medical disclaimer text",
            "recommendation": "Overall recommendation to consult healthcare provider"
        }"""
        
        user_prompt = f"""Here is the interaction data retrieved from medical databases:

        Normalized Medications:
        {json.dumps(normalized_medications, indent=2)}

        Interaction Table:
        {json.dumps(interaction_table, indent=2)}

        User Context:
        {json.dumps(user_context, indent=2) if user_context else "None provided"}

        Citations:
        {json.dumps(citations, indent=2) if citations else "None"}

        Generate a plain-language explanation based ONLY on this data. If the interaction table is empty 
        or contains no meaningful interactions, state that clearly. Do not invent interactions that are 
        not in the data."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Slightly higher for more natural language, but still controlled
                response_format={"type": "json_object"}
            )
            
            explanation = json.loads(response.choices[0].message.content)
            
            # Add metadata
            explanation["metadata"] = {
                "sources_used": interaction_data.get("metadata", {}).get("sources_queried", []),
                "citation_count": len(citations),
                "interaction_count": len(interaction_table)
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

