"""
Main Flask application for Medication Interaction Tracker.
Stateless implementation for Vercel serverless deployment.
"""
from flask import Flask, render_template, request, jsonify, send_from_directory
from agents.query_interpreter import QueryInterpreter
from agents.retrieval_agent import RetrievalAgent
from agents.explanation_agent import ExplanationAgent
from utils.session_manager import get_default_user_context, merge_user_context
from utils.validators import validate_user_query, validate_user_context
from utils.cache_manager import get_cache_manager
from config import Config
import json
import os
import time

# Get the directory of this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path='/static')
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
        except ValueError as e:
            print(f"[CRITICAL] Failed to initialize QueryInterpreter: {str(e)}")
            raise
        except Exception as e:
            print(f"[ERROR] Unexpected error initializing QueryInterpreter: {str(e)}")
            raise
        
        try:
            retrieval_agent = RetrievalAgent()
        except Exception as e:
            print(f"[ERROR] Failed to initialize RetrievalAgent: {str(e)}")
            raise
        
        try:
            explanation_agent = ExplanationAgent()
        except ValueError as e:
            print(f"[CRITICAL] Failed to initialize ExplanationAgent: {str(e)}")
            raise
        except Exception as e:
            print(f"[ERROR] Unexpected error initializing ExplanationAgent: {str(e)}")
            raise
    
    return query_interpreter, retrieval_agent, explanation_agent


@app.route('/')
def index():
    """Render the main chat interface."""
    return render_template('index.html')


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files explicitly."""
    return send_from_directory(STATIC_DIR, filename)


@app.route('/health')
def health_check():
    """Health check endpoint for Vercel."""
    import os
    openai_key = Config.OPENAI_API_KEY
    key_masked = f"***...{openai_key[-10:]}" if openai_key else "NOT SET"
    
    return jsonify({
        "status": "healthy",
        "service": "ExplainRX",
        "openai_configured": bool(Config.OPENAI_API_KEY),
        "openai_key_preview": key_masked,
        "secret_key_configured": bool(Config.SECRET_KEY),
        "flask_env": os.environ.get('FLASK_ENV', 'not set')
    })


@app.route('/api/query', methods=['POST'])
def handle_query():
    """
    Handle user query through the three-agent pipeline with intelligent caching.
    
    Expected JSON:
    {
        "query": "user's natural language question",
        "user_context": {...}  # sent from client-side localStorage
    }
    
    Caching strategy:
    1. Check query cache (exact matches return in <10ms)
    2. Check interaction cache (avoid DrugBank/FDA re-lookups)
    3. Fall through to full pipeline if needed
    """
    start_time = time.time()
    cache = get_cache_manager()
    
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
        
        # ============ ATTEMPT 1: QUERY CACHE HIT ============
        # If exact query was asked before, return cached explanation
        cached_result = cache.get_cached_explanation(user_query)
        if cached_result is not None:
            elapsed = time.time() - start_time
            print(f"[PERFORMANCE] Query cache hit - {elapsed:.3f}s (vs ~5-8s normally)")
            return jsonify({
                "success": True,
                "query_plan": cached_result.get('query_plan'),
                "interaction_data": cached_result.get('interaction_data'),
                "explanation": cached_result.get('explanation'),
                "formatted_explanation": cached_result.get('formatted_explanation'),
                "cache_hit": "query"
            })
        
        # Initialize agents (lazy loading)
        try:
            qi, ra, ea = get_agents()
        except ValueError as e:
            # Missing required API key
            print(f"[CRITICAL] Agent initialization failed: {str(e)}")
            return jsonify({
                "error": "API Configuration Error",
                "details": str(e),
                "message": "The application is not properly configured. Please check that OPENAI_API_KEY is set."
            }), 500
        except Exception as e:
            print(f"[ERROR] Unexpected error during agent initialization: {str(e)}")
            return jsonify({
                "error": "Server Error",
                "details": str(e)
            }), 500
        
        # Agent 1: Query Interpreter
        try:
            query_plan = qi.interpret_query(user_query, user_context)
        except Exception as e:
            print(f"[ERROR] Query interpretation failed: {str(e)}")
            return jsonify({
                "error": "Failed to interpret your query",
                "details": str(e)
            }), 500
        
        if query_plan.get('error'):
            return jsonify({
                "error": "Failed to interpret query",
                "details": query_plan.get('error')
            }), 500
        
        # Agent 2: Retrieval Agent (Deterministic Layer)
        try:
            interaction_data = ra.retrieve_interactions(query_plan)
        except Exception as e:
            print(f"[ERROR] Retrieval failed: {str(e)}")
            return jsonify({
                "error": "Failed to retrieve interaction data",
                "details": str(e)
            }), 500
        
        # Agent 3: Explanation Agent
        try:
            explanation = ea.generate_explanation(
                interaction_data, 
                user_context
            )
        except Exception as e:
            print(f"[ERROR] Explanation generation failed: {str(e)}")
            return jsonify({
                "error": "Failed to generate explanation",
                "details": str(e)
            }), 500
        
        # Format explanation for display
        try:
            formatted_explanation = ea.format_for_display(explanation)
        except Exception as e:
            print(f"[ERROR] Formatting explanation failed: {str(e)}")
            formatted_explanation = None
        
        # ============ CACHE THE RESULT ============
        result = {
            "query_plan": query_plan,
            "interaction_data": interaction_data,
            "explanation": explanation,
            "formatted_explanation": formatted_explanation
        }
        cache.cache_explanation(user_query, result)
        
        elapsed = time.time() - start_time
        print(f"[PERFORMANCE] Full pipeline executed in {elapsed:.2f}s")
        
        return jsonify({
            "success": True,
            **result,
            "cache_hit": None,
            "response_time": f"{elapsed:.2f}s"
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


@app.route('/api/cache-stats', methods=['GET'])
def get_cache_stats():
    """
    Get cache performance statistics.
    
    Returns:
        - Hit rates for query, drug, and interaction caches
        - Cost and time savings estimates
        - Total cached entries
    """
    cache = get_cache_manager()
    stats = cache.get_cache_stats()
    
    return jsonify({
        "success": True,
        "cache_stats": stats,
        "message": "Cache statistics collected. Query the API to generate cache hits."
    })


@app.route('/api/cache-clear', methods=['POST'])
def clear_cache():
    """Clear all caches (useful for testing or resetting stats)."""
    cache = get_cache_manager()
    cache.clear_cache()
    
    return jsonify({
        "success": True,
        "message": "All caches cleared"
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

