"""
Session management utilities for user context.
Supports both server-side sessions (local dev) and client-side storage (Vercel serverless).
"""
from flask import session
from typing import Dict, Optional


def get_user_context() -> Dict:
    """
    Get user context from session or return empty dict.
    For Vercel deployment, this will be supplemented by client-side localStorage.
    
    Returns:
        Dictionary with user context (age, weight, height, medications, conditions)
    """
    return session.get('user_context', {
        'age': None,
        'weight': None,
        'height': None,
        'medications': [],
        'conditions': []
    })


def update_user_context(updates: Dict) -> Dict:
    """
    Update user context in session.
    
    Args:
        updates: Dictionary with fields to update
    
    Returns:
        Updated user context
    """
    context = get_user_context()
    context.update(updates)
    session['user_context'] = context
    return context


def clear_user_context():
    """Clear user context from session."""
    session.pop('user_context', None)

