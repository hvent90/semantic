"""LLM client service for generating skillsets and API descriptions."""

import os
import logging
import json
import asyncio
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path

from services.llm_usage_metrics import LLMProvider, llm_usage_collector, AVAILABLE_MODELS
from models.data_models import ApiInfo, DirectoryAnalysis, AgentsMdContent, TocEntry


logger = logging.getLogger(__name__)


class LLMClient:
    """
    Client for interacting with LLM services to generate skillsets and API descriptions.

    All LLM calls go through the LLM Usage Metrics Collector to ensure usage tracking.
    """

    def __init__(self, provider: LLMProvider = LLMProvider.OPENAI, model: Optional[str] = None):
        """
        Initialize the LLM client.

        Args:
            provider: The LLM provider to use
            model: Specific model to use. If not provided, uses provider default.
        """
        # Try to load .env file if it exists
        self._load_env_file()

        self.provider = provider
        self.model = model or AVAILABLE_MODELS[provider]["default"]

        # Get provider-specific API key
        self.api_key = self._get_api_key_for_provider(provider)

        if not self.api_key:
            logger.warning(f"No API key for {provider.value}. LLM features will be disabled.")
            self._provider_client = None
        else:
            self._provider_client = self._create_provider_client(provider, self.api_key)
            logger.info(f"LLM client initialized with {provider.value} using model {self.model}")

    def _get_api_key_for_provider(self, provider: LLMProvider) -> Optional[str]:
        """Get the API key for the specified provider."""
        key_map = {
            LLMProvider.OPENAI: "OPENAI_API_KEY",
            LLMProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            LLMProvider.GOOGLE: "GOOGLE_API_KEY"
        }
        return os.getenv(key_map[provider])

    def _create_provider_client(self, provider: LLMProvider, api_key: str):
        """Create the appropriate provider client."""
        if provider == LLMProvider.OPENAI:
            from services.providers.openai_provider import OpenAIProvider
            return OpenAIProvider(api_key)
        elif provider == LLMProvider.ANTHROPIC:
            try:
                from services.providers.anthropic_provider import AnthropicProvider
                return AnthropicProvider(api_key)
            except ImportError:
                logger.error("Anthropic library not installed. Install with: pip install anthropic")
                return None
        elif provider == LLMProvider.GOOGLE:
            try:
                from services.providers.google_provider import GoogleProvider
                return GoogleProvider(api_key)
            except ImportError:
                logger.error("Google Generative AI library not installed. Install with: pip install google-generativeai")
                return None
        else:
            logger.error(f"Unknown provider: {provider}")
            return None
    
    def _load_env_file(self):
        """Load environment variables from .env file if it exists."""
        env_path = Path.cwd() / ".env"
        if env_path.exists():
            try:
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            os.environ[key] = value
                logger.debug(f"Loaded environment variables from {env_path}")
            except Exception as e:
                logger.debug(f"Could not load .env file: {e}")
        else:
            logger.debug("No .env file found")
    
    def is_available(self) -> bool:
        """Check if LLM client is available for use."""
        return self._provider_client is not None and self._provider_client.is_available()

    def summarize(self, prompt: str) -> str:
        return self._make_llm_request(prompt, 5000, "summary")

    async def summarize_async(self, prompt: str) -> str:
        """Async version of summarize method."""
        return await self._make_llm_request_async(prompt, 5000, "summary")
    
    def _make_llm_request(self, prompt: str, max_output_tokens: int, operation_type: str, model: Optional[str] = None) -> str:
        """
        Centralized function to make LLM API requests using provider abstraction.

        Args:
            prompt: The input prompt for the LLM
            max_output_tokens: Maximum number of tokens to generate
            operation_type: Type of operation for usage tracking
            model: The model to use (defaults to instance model)

        Returns:
            The text response from the LLM

        Raises:
            Exception: If the API call fails or client is not available
        """
        if not self.is_available():
            raise Exception("LLM client is not available")

        model_to_use = model or self.model

        try:
            response = self._provider_client.create_completion(prompt, model_to_use, max_output_tokens)

            # Track usage metrics
            llm_usage_collector.log_usage(
                provider=self.provider,
                model=model_to_use,
                input_tokens=response["input_tokens"],
                output_tokens=response["output_tokens"],
                operation_type=operation_type
            )

            return response["text"]

        except Exception as e:
            logger.error(f"Error making LLM request ({operation_type}): {e}")
            raise
    
    async def _make_llm_request_async(self, prompt: str, max_output_tokens: int, operation_type: str, model: Optional[str] = None) -> str:
        """
        Async version of the centralized function to make LLM API requests.

        Args:
            prompt: The input prompt for the LLM
            max_output_tokens: Maximum number of tokens to generate
            operation_type: Type of operation for usage tracking
            model: The model to use (defaults to instance model)

        Returns:
            The text response from the LLM

        Raises:
            Exception: If the API call fails or client is not available
        """
        if not self.is_available():
            raise Exception("LLM client is not available")

        model_to_use = model or self.model

        try:
            # Run the provider call in a thread pool to make it async
            loop = asyncio.get_event_loop()

            def _sync_request():
                response = self._provider_client.create_completion(prompt, model_to_use, max_output_tokens)

                # Track usage metrics
                llm_usage_collector.log_usage(
                    provider=self.provider,
                    model=model_to_use,
                    input_tokens=response["input_tokens"],
                    output_tokens=response["output_tokens"],
                    operation_type=operation_type
                )

                return response["text"]

            return await loop.run_in_executor(None, _sync_request)

        except Exception as e:
            logger.error(f"Error making async LLM request ({operation_type}): {e}")
            raise

# Global instance to be used across the application  
llm_client = LLMClient()