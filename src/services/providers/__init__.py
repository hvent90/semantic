"""Provider abstraction layer for LLM services."""

from abc import ABC, abstractmethod
from typing import Dict, Any


class LLMProviderClient(ABC):
    """Abstract base class for LLM provider clients."""

    @abstractmethod
    def create_completion(self, prompt: str, model: str, max_tokens: int) -> Dict[str, Any]:
        """Create a completion using provider-specific API."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider client is available."""
        pass