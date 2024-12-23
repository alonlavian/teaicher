"""
Module for handling AI service interactions (Claude and Tavily).
"""
from typing import Optional, Dict, Any, Union
import logging
import os
from anthropic import Anthropic
from tavily import TavilyClient
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv
import pathlib

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables before initializing clients
current_dir = pathlib.Path(__file__).parent.resolve()
env_path = current_dir / '.env'
logger.debug(f"Looking for .env file at: {env_path}")
load_dotenv(env_path)

# Log environment variables (safely)
logger.debug("Environment variables loaded:")
logger.debug(f"ANTHROPIC_API_KEY present: {'ANTHROPIC_API_KEY' in os.environ}")
logger.debug(f"TAVILY_API_KEY present: {'TAVILY_API_KEY' in os.environ}")

# Initialize clients with better error handling
def get_tavily_client():
    api_key = os.getenv('TAVILY_API_KEY')
    if not api_key:
        return None
    return TavilyClient(api_key=api_key)

def get_anthropic_client():
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        return None
    return Anthropic(api_key=api_key)

_anthropic_client = None
_tavily_client = None

def get_clients():
    global _anthropic_client, _tavily_client
    if _anthropic_client is None:
        _anthropic_client = get_anthropic_client()
    if _tavily_client is None:
        _tavily_client = get_tavily_client()
    return _anthropic_client, _tavily_client

class AIServiceError(Exception):
    """Custom exception for AI service related errors."""
    pass

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_claude(
    query: str,
    context: Optional[str] = None,
    model: str = "claude-3-sonnet-20240229",
    max_tokens: int = 512,
    dry_run: bool = False,
    language: str = 'en'
):
    """
    Call Claude API with retry mechanism and proper error handling.
    
    Args:
        query: User query to process
        context: Optional context to include in the system prompt
        model: Claude model to use
        max_tokens: Maximum tokens in response
        dry_run: If True, return mock response
        language: Language for the response (en, he, etc.)
    
    Returns:
        str: Claude's response
    
    Raises:
        AIServiceError: If the API call fails after retries
    """
    if dry_run:
        return "This is a mock response from Claude for testing purposes."
    
    anthropic_client, _ = get_clients()
    if not anthropic_client:
        raise AIServiceError("Anthropic client not initialized - missing API key")
        
    try:
        # Prepare system message and user message based on language
        if language == 'he':
            system = "אתה מורה למתמטיקה מסור ועוזר. עליך לענות בעברית בלבד."
            if context:
                system += f"\n\nהקשר: {context}"
        else:
            system = "You are a helpful math tutor."
            if context:
                system += f"\n\nContext: {context}"
            
        response = anthropic_client.messages.create(
            model=model,
            system=system,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": query
                }
            ]
        )
        
        return response.content[0].text
        
    except Exception as e:
        logger.error(f"Error calling Claude API: {str(e)}")
        raise AIServiceError(f"Failed to get response from Claude: {str(e)}")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_tavily_search(query: str, dry_run: bool = False):
    """
    Call Tavily web search API with retry mechanism.
    
    Args:
        query: Search query
        dry_run: If True, return mock response
    
    Returns:
        str: Search results
    
    Raises:
        AIServiceError: If the API call fails after retries
    """
    if dry_run:
        return "This is a mock response from Tavily Search for testing purposes."
    
    _, tavily_client = get_clients()
    if not tavily_client:
        raise AIServiceError("Tavily client not initialized - missing API key")
        
    try:
        response = tavily_client.search(query=query)
        return response
    except Exception as e:
        logger.error(f"Error calling Tavily API: {str(e)}")
        raise AIServiceError(f"Failed to get search results: {str(e)}")

def generate_math_problem(subject: str, language: str = 'en') -> dict:
    """
    Generate a math problem using Claude in the specified language.
    
    Args:
        subject: The math subject (algebra, geometry, etc.)
        language: The language to generate the problem in (en, he, etc.)
    
    Returns:
        dict: Contains 'question' and 'answer' keys
    """
    if language == 'he':
        prompt = f"""צור שאלה במתמטיקה בנושא {subject}. 
        התשובה חייבת להיות בפורמט JSON המדויק הבא:
        {{
            "question": "טקסט השאלה",
            "answer": "התשובה המספרית או הפתרון הקצר"
        }}
        וודא שהשאלה מתאימה לרמת תיכון.
        השתמש בפורמט RTL נכון.
        חשוב: התשובה צריכה להיות מדויקת ומספרית ככל האפשר."""
    else:
        prompt = f"""Generate a {subject} math problem. 
        The response should be in this exact JSON format:
        {{
            "question": "the problem text",
            "answer": "the numerical answer or short solution"
        }}
        Make sure the problem is appropriate for high school level.
        Important: The answer should be as precise and numerical as possible."""
    
    try:
        response = call_claude(prompt, max_tokens=256, language=language)
        # Extract the JSON part from the response
        import json
        import re
        
        # Find JSON-like content between curly braces
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            problem_dict = json.loads(json_match.group())
            return problem_dict
        else:
            raise AIServiceError("Failed to parse JSON from Claude's response")
            
    except Exception as e:
        logger.error(f"Error generating math problem: {e}")
        # Fallback problem in case of error
        if language == 'he':
            return {
                "question": "כמה זה 15 + 27?",
                "answer": "42"
            }
        return {
            "question": "What is 15 + 27?",
            "answer": "42"
        }
