"""
Agent 1: Query Interpreter
Extracts structured information from natural language queries about medications.
"""
import json
import sys
from config import Config
from utils.openai_client import initialize_openai_client, cleanup_environment

# Cleanup environment on module load
cleanup_environment()


class QueryInterpreter:
    """Interprets natural language queries and extracts structured medication information."""
    
    def __init__(self):
        """Initialize the query interpreter with OpenAI client."""
        print(f"[DEBUG] Python version: {sys.version}", file=sys.stderr)
        self.client = initialize_openai_client("QueryInterpreter")
        self.model = Config.OPENAI_MODEL
    
    def interpret_query(self, user_query: str, user_context: dict = None) -> dict:
        """
        Interpret a natural language query and extract structured information.
        
        Args:
            user_query: The user's natural language question
            user_context: Optional user context (age, weight, height, existing meds, conditions)
        
        Returns:
            Dictionary with structured query information
        """
        if user_context is None:
            user_context = {}
        
        system_prompt = """You are a medical query interpreter. Your job is to extract structured information 
        from natural language questions about medications, foods, supplements, and their interactions.

        Extract the following information:
        - medications: List of all medications mentioned (both prescription and OTC)
        - foods: List of foods or beverages mentioned
        - supplements: List of supplements or vitamins mentioned
        - query_type: Type of query (e.g., "interaction_check", "safety_check", "food_interaction", "supplement_interaction")
        - query_focus: What the user is specifically asking about:
            * "medication_safety" if asking if a single medication is safe (especially with health conditions)
            * "food" if asking about a specific food/beverage with medications
            * "supplement" if asking about a specific supplement with medications
            * "drug_drug" if asking about interactions between 2+ medications
            * "general" if asking for general medication information
        - user_context: Any relevant user information from the query (age, weight, conditions mentioned)

        Return ONLY valid JSON in this exact format:
        {
            "medications": ["medication1", "medication2"],
            "foods": ["food1"],
            "supplements": ["supplement1"],
            "query_type": "interaction_check",
            "query_focus": "medication_safety",
            "user_context": {}
        }

        If information is not mentioned, use empty lists or empty objects. Be precise and only extract 
        what is explicitly stated or clearly implied.
        
        IMPORTANT: Set query_focus correctly:
        - If user asks "Can I take [single drug]?" OR "Is [drug] safe for me?" OR "What [drug type] is safe?" OR "What would be a better [drug type]?": set to "medication_safety"
        - If user mentions a specific food/beverage (grapefruit, alcohol, etc): set to "food"
        - If user mentions a specific supplement: set to "supplement"
        - If user is asking about 2+ medications together: set to "drug_drug"
        - If user is asking for alternative medications or safer options: set to "medication_safety"
        - Otherwise: set to "general"
        """
        
        user_prompt = f"""User query: "{user_query}"

        Existing user context: {json.dumps(user_context, indent=2) if user_context else "None"}

        Extract the structured information from this query."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=500  # Limit tokens for faster response
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Merge with existing user context
            # User's persistent profile (from localStorage) takes precedence over LLM-extracted context
            if user_context:
                # LLM-extracted context first, then user's saved profile overrides it
                result["user_context"] = {**result.get("user_context", {}), **user_context}
            
            return result
            
        except json.JSONDecodeError as e:
            # Fallback if JSON parsing fails
            return {
                "medications": [],
                "foods": [],
                "supplements": [],
                "query_type": "interaction_check",
                "query_focus": "general",
                "user_context": user_context or {},
                "error": f"Failed to parse response: {str(e)}"
            }
        except Exception as e:
            return {
                "medications": [],
                "foods": [],
                "supplements": [],
                "query_type": "interaction_check",
                "query_focus": "general",
                "user_context": user_context or {},
                "error": f"Error interpreting query: {str(e)}"
            }

