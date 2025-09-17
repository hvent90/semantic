"""OpenAI provider implementation."""

from typing import Dict, Any
from openai import OpenAI
from . import LLMProviderClient


class OpenAIProvider(LLMProviderClient):
    """OpenAI provider client implementation."""

    def __init__(self, api_key: str):
        """Initialize OpenAI provider with API key."""
        self._client = OpenAI(api_key=api_key)

    def create_completion(self, prompt: str, model: str, max_tokens: int) -> Dict[str, Any]:
        """Create a completion using OpenAI API."""
        response = self._client.responses.create(
            model=model,
            input=prompt,
            max_output_tokens=max_tokens,
            reasoning={"effort": "minimal"},
            text={"verbosity": "low"}
        )
        return {
            "text": response.output_text,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens
        }

    def is_available(self) -> bool:
        """Check if OpenAI client is available."""
        return self._client is not None