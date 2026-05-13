import os
import logging
from groq import Groq
from .config import get_local_llm

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"

_groq_client = None

def get_groq_client():
    """Lazy initialization of Groq client."""
    global _groq_client
    if _groq_client is None and GROQ_API_KEY:
        try:
            _groq_client = Groq(api_key=GROQ_API_KEY)
            logger.info("Groq client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
    return _groq_client

def call_llm(prompt: str, system_prompt: str = "You are a professional assistant.") -> str:
    """ Unified helper to call the best available LLM (Groq -> Local)."""
    client = get_groq_client()
    if client:
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Groq call failed, falling back to local: {e}")
    
    # Fallback to local Ollama
    local_llm = get_local_llm()
    try:
        response = local_llm.invoke(f"{system_prompt}\n\nUser: {prompt}")
        return response.content
    except Exception as e:
        logger.error(f"Local LLM fallback also failed: {e}")
        return ""
