"""
Main Flask application for Medication Interaction Tracker.
"""
from flask import Flask, render_template, request, jsonify, session
from agents.query_interpreter import QueryInterpreter
from agents.retrieval_agent import RetrievalAgent
from agents.explanation_agent import ExplanationAgent
from utils.session_manager import get_user_context, update_user_context
from utils.validators import validate_user_query, validate_user_context
from config import Config
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Initialize agents
query_interpreter = QueryInterpreter()
retrieval_agent = RetrievalAgent()
explanation_agent = ExplanationAgent()


@app.route('/')
def index():
    """Render the main chat interface."""
    return render_template('index.html')


@app.route('/api/query', methods=['POST'])
def handle_query():
    """
    Handle user query through the three-agent pipeline.
    
    Expected JSON:
    {
        "query": "user's natural language question",
        "user_context": {...}  # optional, can also come from session
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
        
        # Get user context (from request or session)
        user_context = data.get('user_context') or get_user_context()
        
        # Agent 1: Query Interpreter
        query_plan = query_interpreter.interpret_query(user_query, user_context)
        
        if query_plan.get('error'):
            return jsonify({
                "error": "Failed to interpret query",
                "details": query_plan.get('error')
            }), 500
        
        # Agent 2: Retrieval Agent (Deterministic Layer)
        interaction_data = retrieval_agent.retrieve_interactions(query_plan)
        
        # Agent 3: Explanation Agent
        explanation = explanation_agent.generate_explanation(
            interaction_data, 
            user_context
        )
        
        # Format explanation for display
        formatted_explanation = explanation_agent.format_for_display(explanation)
        
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
    
    GET: Returns current user context
    POST: Updates user context
        Expected JSON: {"age": ..., "weight": ..., "height": ..., "medications": [...], "conditions": [...]}
    """
    if request.method == 'GET':
        return jsonify({
            "success": True,
            "user_context": get_user_context()
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
            
            # Update context
            updated_context = update_user_context(data)
            
            return jsonify({
                "success": True,
                "user_context": updated_context,
                "message": "Profile updated successfully"
            })
            
        except Exception as e:
            return jsonify({
                "error": "Failed to update profile",
                "details": str(e)
            }), 500


@app.route('/api/clear-profile', methods=['POST'])
def clear_profile():
    """Clear user profile/context."""
    from utils.session_manager import clear_user_context
    clear_user_context()
    return jsonify({
        "success": True,
        "message": "Profile cleared"
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

