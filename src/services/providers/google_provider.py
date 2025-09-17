"""Google provider implementation."""

from typing import Dict, Any
import google.generativeai as genai
from . import LLMProviderClient


class GoogleProvider(LLMProviderClient):
    """Google provider client implementation."""

    def __init__(self, api_key: str):
        """Initialize Google provider with API key."""
        genai.configure(api_key=api_key)
        self._client = genai.GenerativeModel()

    def create_completion(self, prompt: str, model: str, max_tokens: int) -> Dict[str, Any]:
        """Create a completion using Google Gemini API."""
        # Configure the model with the specified model name
        self._client = genai.GenerativeModel(model)

        response = self._client.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens
            )
        )
        # Note: Google API token counting may need separate implementation
        return {
            "text": response.text,
            "input_tokens": len(prompt.split()) * 1.3,  # Rough estimation
            "output_tokens": len(response.text.split()) * 1.3
        }

    def is_available(self) -> bool:
        """Check if Google client is available."""
        return self._client is not None