"""
NLP Query Parser

Parses natural language questions about medication safety using an LLM.
Extracts medications, supplements, and food items from user queries.
"""

import os
import json
from typing import Dict, List, Optional
from openai import OpenAI


class QueryParser:
    """Parses natural language queries about medication interactions."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the query parser.
        
        Args:
            api_key: OpenAI API key. If not provided, reads from OPENAI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
    
    def parse_query(self, user_query: str) -> Dict:
        """
        Parse a natural language query to extract medications, supplements, and foods.
        
        Args:
            user_query: User's natural language question
            
        Returns:
            Dictionary with parsed entities:
            {
                "medications": [],
                "supplements": [],
                "foods": [],
                "query_type": "interaction_check|safety_info|general",
                "original_query": str
            }
        """
        if not self.client:
            # Fallback to basic parsing if no API key
            return self._basic_parse(user_query)
        
        system_prompt = """You are a medical query parser. Extract medications, supplements, and food items from user queries.
Return a JSON object with this structure:
{
    "medications": ["list of drug names"],
    "supplements": ["list of supplements"],
    "foods": ["list of foods"],
    "query_type": "interaction_check" or "safety_info" or "general"
}

Examples:
- "Can I take aspirin with ibuprofen?" -> medications: ["aspirin", "ibuprofen"], query_type: "interaction_check"
- "Is it safe to eat grapefruit while on statins?" -> medications: ["statins"], foods: ["grapefruit"], query_type: "interaction_check"
- "What supplements interact with warfarin?" -> medications: ["warfarin"], query_type: "interaction_check"
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            parsed_data = json.loads(response.choices[0].message.content)
            parsed_data["original_query"] = user_query
            
            # Ensure all required fields exist
            parsed_data.setdefault("medications", [])
            parsed_data.setdefault("supplements", [])
            parsed_data.setdefault("foods", [])
            parsed_data.setdefault("query_type", "general")
            
            return parsed_data
            
        except Exception as e:
            print(f"Error parsing query with LLM: {e}")
            return self._basic_parse(user_query)
    
    def _basic_parse(self, user_query: str) -> Dict:
        """
        Fallback parser using simple keyword matching.
        
        Args:
            user_query: User's question
            
        Returns:
            Dictionary with basic parsed data
        """
        query_lower = user_query.lower()
        
        # Common medications (for demo purposes)
        common_meds = [
            "aspirin", "ibuprofen", "acetaminophen", "warfarin", 
            "metformin", "lisinopril", "atorvastatin", "statins",
            "levothyroxine", "metoprolol", "omeprazole"
        ]
        
        # Common supplements
        common_supplements = [
            "vitamin d", "vitamin c", "calcium", "iron", "fish oil",
            "omega-3", "magnesium", "zinc", "st john's wort"
        ]
        
        # Common problematic foods
        common_foods = [
            "grapefruit", "alcohol", "caffeine", "dairy", "leafy greens"
        ]
        
        medications = [med for med in common_meds if med in query_lower]
        supplements = [supp for supp in common_supplements if supp in query_lower]
        foods = [food for food in common_foods if food in query_lower]
        
        # Determine query type
        interaction_keywords = ["interact", "take with", "take", "combine", "safe", "together", "with"]
        query_type = "interaction_check" if any(kw in query_lower for kw in interaction_keywords) else "general"
        
        return {
            "medications": medications,
            "supplements": supplements,
            "foods": foods,
            "query_type": query_type,
            "original_query": user_query
        }
