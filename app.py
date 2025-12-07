"""
Main Flask application for Medication Interaction Tracker.
Stateless implementation for Vercel serverless deployment.
"""
from flask import Flask, render_template, request, jsonify
from agents.query_interpreter import QueryInterpreter
from agents.retrieval_agent import RetrievalAgent
from agents.explanation_agent import ExplanationAgent
from utils.session_manager import get_default_user_context, merge_user_context
from utils.validators import validate_user_query, validate_user_context
from config import Config
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Initialize agents (lazy loading for better error handling)
query_interpreter = None
retrieval_agent = None
explanation_agent = None

def get_agents():
    """Lazy initialization of agents to handle missing API keys gracefully."""
    global query_interpreter, retrieval_agent, explanation_agent
    
    if query_interpreter is None:
        try:
            query_interpreter = QueryInterpreter()
            retrieval_agent = RetrievalAgent()
            explanation_agent = ExplanationAgent()
        except Exception as e:
            print(f"Error initializing agents: {str(e)}")
            raise
    
    return query_interpreter, retrieval_agent, explanation_agent


@app.route('/')
def index():
    """Render the main chat interface."""
    return render_template('index.html')


@app.route('/health')
def health_check():
    """Health check endpoint for Vercel."""
    return jsonify({
        "status": "healthy",
        "service": "ExplainRX",
        "openai_configured": bool(Config.OPENAI_API_KEY),
        "secret_key_configured": bool(Config.SECRET_KEY)
    })


@app.route('/api/query', methods=['POST'])
def handle_query():
    """
    Handle user query through the three-agent pipeline.
    
    Expected JSON:
    {
        "query": "user's natural language question",
        "user_context": {...}  # sent from client-side localStorage
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        user_query = data.get('query', '').strip()
        
        # Validate query
        is_valid, error_msg = validate_user_query(user_query)
        if not is_valid:
            return jsonify({"error": error_msg}), 400
        
        # Get user context from request (client-side localStorage)
        # Default to empty context if not provided
        user_context = data.get('user_context') or get_default_user_context()
        
        # Initialize agents (lazy loading)
        qi, ra, ea = get_agents()
        
        # Agent 1: Query Interpreter
        query_plan = qi.interpret_query(user_query, user_context)
        
        if query_plan.get('error'):
            return jsonify({
                "error": "Failed to interpret query",
                "details": query_plan.get('error')
            }), 500
        
        # Agent 2: Retrieval Agent (Deterministic Layer)
        interaction_data = ra.retrieve_interactions(query_plan)
        
        # Agent 3: Explanation Agent
        explanation = ea.generate_explanation(
            interaction_data, 
            user_context
        )
        
        # Format explanation for display
        formatted_explanation = ea.format_for_display(explanation)
        
        return jsonify({
            "success": True,
            "query_plan": query_plan,
            "interaction_data": interaction_data,
            "explanation": explanation,
            "formatted_explanation": formatted_explanation
        })
        
    except Exception as e:
        return jsonify({
            "error": "An error occurred processing your query",
            "details": str(e)
        }), 500


@app.route('/api/profile', methods=['GET', 'POST'])
def handle_profile():
    """
    Get or update user profile/context.
    
    GET: Returns default empty context structure (client should use localStorage)
    POST: Validates and returns merged context (client stores in localStorage)
        Expected JSON: {"age": ..., "weight": ..., "height": ..., "medications": [...], "conditions": [...]}
    """
    if request.method == 'GET':
        # Return default structure - actual context comes from client localStorage
        return jsonify({
            "success": True,
            "user_context": get_default_user_context(),
            "message": "Use client-side localStorage for persistent storage"
        })
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            # Validate context
            is_valid, error_msg = validate_user_context(data)
            if not is_valid:
                return jsonify({"error": error_msg}), 400
            
            # Merge with defaults and return (client stores in localStorage)
            # This is stateless - we don't store on server
            updated_context = merge_user_context(updates=data)
            
            return jsonify({
                "success": True,
                "user_context": updated_context,
                "message": "Profile validated successfully. Store in localStorage on client."
            })
            
        except Exception as e:
            return jsonify({
                "error": "Failed to validate profile",
                "details": str(e)
            }), 500


@app.route('/api/clear-profile', methods=['POST'])
def clear_profile():
    """
    Clear user profile/context.
    Returns default empty context - client should clear localStorage.
    """
    return jsonify({
        "success": True,
        "user_context": get_default_user_context(),
        "message": "Profile cleared. Clear localStorage on client."
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

