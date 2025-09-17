"""Anthropic provider implementation."""

from typing import Dict, Any
import anthropic
from . import LLMProviderClient


class AnthropicProvider(LLMProviderClient):
    """Anthropic provider client implementation."""

    def __init__(self, api_key: str):
        """Initialize Anthropic provider with API key."""
        self._client = anthropic.Anthropic(api_key=api_key)

    def create_completion(self, prompt: str, model: str, max_tokens: int) -> Dict[str, Any]:
        """Create a completion using Anthropic API."""
        response = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return {
            "text": response.content[0].text,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens
        }

    def is_available(self) -> bool:
        """Check if Anthropic client is available."""
        return self._client is not None