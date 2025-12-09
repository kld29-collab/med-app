"""
Session management utilities for user context.
Stateless implementation for Vercel serverless deployment.
User context is stored client-side (localStorage) and sent with each request.
"""
from typing import Dict


def get_default_user_context() -> Dict:
    """
    Get default empty user context.
    For Vercel serverless, user context comes from request payload (client-side localStorage).
    
    Returns:
        Dictionary with default empty user context structure
    """
    return {
        'age': None,
        'sex': None,
        'weight': None,
        'height': None,
        'medications': [],
        'conditions': []
    }


def merge_user_context(existing: Dict = None, updates: Dict = None) -> Dict:
    """
    Merge user context updates with existing context.
    This is a stateless operation - no server-side storage.
    
    Args:
        existing: Existing user context (from request)
        updates: Dictionary with fields to update
    
    Returns:
        Merged user context
    """
    if existing is None:
        existing = get_default_user_context()
    if updates is None:
        updates = {}
    
    context = existing.copy()
    context.update(updates)
    return context

