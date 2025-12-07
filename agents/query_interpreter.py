"""
Agent 1: Query Interpreter
Extracts structured information from natural language queries about medications.
"""
import json
import os
import sys
from openai import OpenAI
from config import Config

# Disable environment variable auto-detection that might cause issues
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)


class QueryInterpreter:
    """Interprets natural language queries and extracts structured medication information."""
    
    def __init__(self):
        """Initialize the query interpreter with OpenAI client."""
        print(f"[DEBUG] Python version: {sys.version}", file=sys.stderr)
        
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured. Please set it in your environment variables.")
        
        try:
            print(f"[DEBUG] Initializing OpenAI client...", file=sys.stderr)
            # Initialize OpenAI client - try with minimal config first
            import httpx
            
            # Create a custom HTTP client without proxy
            http_client = httpx.Client(
                timeout=30.0,
                verify=True,
                proxies=None  # Explicitly set to None
            )
            
            self.client = OpenAI(
                api_key=Config.OPENAI_API_KEY,
                http_client=http_client
            )
            print(f"[DEBUG] OpenAI client initialized successfully with custom http_client", file=sys.stderr)
        except Exception as e:
            print(f"[ERROR] Failed with custom http_client, trying basic init: {str(e)}", file=sys.stderr)
            try:
                # Fallback: try without http_client parameter
                self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
                print(f"[DEBUG] OpenAI client initialized successfully with basic init", file=sys.stderr)
            except Exception as e2:
                print(f"[ERROR] Basic init also failed: {str(e2)}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
                raise ValueError(f"Failed to initialize OpenAI client: {str(e2)}")
        
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
        - query_type: Type of query (e.g., "interaction_check", "food_interaction", "supplement_interaction")
        - user_context: Any relevant user information from the query (age, weight, conditions mentioned)

        Return ONLY valid JSON in this exact format:
        {
            "medications": ["medication1", "medication2"],
            "foods": ["food1"],
            "supplements": ["supplement1"],
            "query_type": "interaction_check",
            "user_context": {}
        }

        If information is not mentioned, use empty lists or empty objects. Be precise and only extract 
        what is explicitly stated or clearly implied."""
        
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
                temperature=0.1  # Low temperature for consistent extraction
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
                "user_context": user_context or {},
                "error": f"Failed to parse response: {str(e)}"
            }
        except Exception as e:
            return {
                "medications": [],
                "foods": [],
                "supplements": [],
                "query_type": "interaction_check",
                "user_context": user_context or {},
                "error": f"Error interpreting query: {str(e)}"
            }

