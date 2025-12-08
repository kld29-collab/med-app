"""
Shared OpenAI client initialization utility.
Eliminates duplicate client setup code in agents.
"""
import os
import sys
from openai import OpenAI
from config import Config


def initialize_openai_client(agent_name: str = "Agent") -> OpenAI:
    """
    Initialize OpenAI client with robust error handling.
    
    Handles both httpx custom client and fallback to basic initialization.
    Used by QueryInterpreter and ExplanationAgent to avoid code duplication.
    
    Args:
        agent_name: Name of agent initializing client (for debug messages)
    
    Returns:
        Initialized OpenAI client
    
    Raises:
        ValueError: If API key not configured or both init methods fail
    """
    if not Config.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not configured. Please set it in your environment variables.")
    
    try:
        print(f"[DEBUG] Initializing OpenAI client in {agent_name}...", file=sys.stderr)
        # Initialize OpenAI client - try with minimal config first
        import httpx
        
        # Create a custom HTTP client without proxy
        http_client = httpx.Client(
            timeout=30.0,
            verify=True,
            proxies=None  # Explicitly set to None
        )
        
        client = OpenAI(
            api_key=Config.OPENAI_API_KEY,
            http_client=http_client
        )
        print(f"[DEBUG] OpenAI client in {agent_name} initialized successfully with custom http_client", file=sys.stderr)
        return client
    except Exception as e:
        print(f"[ERROR] Failed with custom http_client, trying basic init: {str(e)}", file=sys.stderr)
        try:
            # Fallback: try without http_client parameter
            client = OpenAI(api_key=Config.OPENAI_API_KEY)
            print(f"[DEBUG] OpenAI client in {agent_name} initialized successfully with basic init", file=sys.stderr)
            return client
        except Exception as e2:
            print(f"[ERROR] Basic init also failed: {str(e2)}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            raise ValueError(f"Failed to initialize OpenAI client: {str(e2)}")


def cleanup_environment():
    """
    Clean up environment variables that might interfere with HTTP requests.
    Call this once at module load time to avoid proxy issues.
    """
    os.environ.pop('HTTP_PROXY', None)
    os.environ.pop('HTTPS_PROXY', None)
    os.environ.pop('http_proxy', None)
    os.environ.pop('https_proxy', None)
