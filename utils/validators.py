"""
Input validation utilities.
"""
from typing import Dict, List, Optional


def validate_user_query(query: str, max_length: int = 500) -> tuple[bool, Optional[str]]:
    """
    Validate user query input.
    
    Args:
        query: User's query string
        max_length: Maximum allowed length
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not query or not query.strip():
        return False, "Query cannot be empty"
    
    if len(query) > max_length:
        return False, f"Query exceeds maximum length of {max_length} characters"
    
    return True, None


def validate_user_context(context: Dict) -> tuple[bool, Optional[str]]:
    """
    Validate user context data.
    
    Args:
        context: User context dictionary
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if 'age' in context and context['age'] is not None:
        try:
            age = int(context['age'])
            if age < 0 or age > 150:
                return False, "Age must be between 0 and 150"
        except (ValueError, TypeError):
            return False, "Age must be a valid number"
    
    if 'weight' in context and context['weight'] is not None:
        try:
            weight = float(context['weight'])
            if weight < 0 or weight > 1000:
                return False, "Weight must be between 0 and 1000"
        except (ValueError, TypeError):
            return False, "Weight must be a valid number"
    
    if 'height' in context and context['height'] is not None:
        try:
            height = float(context['height'])
            if height < 0 or height > 300:
                return False, "Height must be between 0 and 300 cm"
        except (ValueError, TypeError):
            return False, "Height must be a valid number"
    
    if 'medications' in context:
        if not isinstance(context['medications'], list):
            return False, "Medications must be a list"
    
    if 'conditions' in context:
        if not isinstance(context['conditions'], list):
            return False, "Conditions must be a list"
    
    return True, None

