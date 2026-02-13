from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class LLMProvider(ABC):
    """
    Abstract Base Class for LLM Providers.
    
    DEFINES:
    - Standard interface for all models (Gemini, OpenAI, Ollama)
    - Unified error handling and retry wrappers
    - Consistent response schema (Plan, Code, Debug)
    """
    
    @abstractmethod
    def generate_response(self, prompt: str, system_instruction: Optional[str] = None, temperature: float = 0.7) -> str:
        """Generate a raw text response from the model."""
        pass

    @abstractmethod
    def generate_json(self, prompt: str, schema: Dict[str, Any], system_instruction: Optional[str] = None) -> Dict[str, Any]:
        """Generate structured JSON response matching a schema."""
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__}>"
