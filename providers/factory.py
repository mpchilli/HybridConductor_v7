from typing import Optional, Dict, Any
from .gemini import GeminiProvider
# from .openai import OpenAIProvider  # Future
# from .ollama import OllamaProvider  # Future

def get_provider(provider_type: str, **kwargs) -> any:
    """
    Factory method to instantiate the correct LLM provider.
    """
    p_type = provider_type.lower()
    
    if p_type == "gemini":
        return GeminiProvider(**kwargs)
    elif p_type == "openai":
        from .openai import OpenAIProvider
        return OpenAIProvider(**kwargs)
    elif p_type == "ollama":
        # return OllamaProvider(**kwargs)
        return GeminiProvider(**kwargs) # Fallback for now
        
    raise ValueError(f"Unknown provider type: {provider_type}")
