"""LLM client service for generating skillsets and API descriptions."""

import os
import logging
import json
import asyncio
from typing import List, Optional, Tuple, Dict, Any
from openai import OpenAI
from pathlib import Path

from services.llm_usage_metrics import LLMProvider, llm_usage_collector
from models.data_models import ApiInfo, DirectoryAnalysis, AgentsMdContent, TocEntry


logger = logging.getLogger(__name__)


class LLMClient:
    """
    Client for interacting with LLM services to generate skillsets and API descriptions.
    
    All LLM calls go through the LLM Usage Metrics Collector to ensure usage tracking.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LLM client.
        
        Args:
            api_key: OpenAI API key. If not provided, will try to get from environment.
        """
        # Try to load .env file if it exists
        self._load_env_file()
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("No OpenAI API key provided. LLM features will be disabled.")
            self._client = None
        else:
            self._client = OpenAI(api_key=self.api_key)
            logger.info("LLM client initialized with OpenAI")
    
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
        return self._client is not None

    def summarize(self, prompt: str) -> str:
        return self._make_llm_request(prompt, 5000, "summary", "gpt-5-nano")
    
    async def summarize_async(self, prompt: str) -> str:
        """Async version of summarize method."""
        return await self._make_llm_request_async(prompt, 5000, "summary", "gpt-5-nano")
    
    def _make_llm_request(self, prompt: str, max_output_tokens: int, operation_type: str, model: str = "gpt-5-nano") -> str:
        """
        Centralized function to make OpenAI API requests using the Responses API.
        
        Args:
            prompt: The input prompt for the LLM
            max_output_tokens: Maximum number of tokens to generate
            operation_type: Type of operation for usage tracking
            model: The model to use (defaults to gpt-5-mini)
            
        Returns:
            The text response from the LLM
            
        Raises:
            Exception: If the API call fails or client is not available
        """
        if not self.is_available():
            raise Exception("LLM client is not available")
        
        try:
            response = self._client.responses.create(
                model=model,
                input=prompt,
                max_output_tokens=max_output_tokens,
                reasoning={"effort": "minimal"},
                text={"verbosity": "low"}
            )
            
            # Track usage metrics
            llm_usage_collector.log_usage(
                provider=LLMProvider.OPENAI,
                model=model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                operation_type=operation_type
            )
            
            return response.output_text
            
        except Exception as e:
            logger.error(f"Error making LLM request ({operation_type}): {e}")
            raise
    
    async def _make_llm_request_async(self, prompt: str, max_output_tokens: int, operation_type: str, model: str = "gpt-5-nano") -> str:
        """
        Async version of the centralized function to make OpenAI API requests.
        
        Args:
            prompt: The input prompt for the LLM
            max_output_tokens: Maximum number of tokens to generate
            operation_type: Type of operation for usage tracking
            model: The model to use (defaults to gpt-5-nano)
            
        Returns:
            The text response from the LLM
            
        Raises:
            Exception: If the API call fails or client is not available
        """
        if not self.is_available():
            raise Exception("LLM client is not available")
        
        try:
            # Run the synchronous OpenAI call in a thread pool to make it async
            loop = asyncio.get_event_loop()
            
            def _sync_request():
                response = self._client.responses.create(
                    model=model,
                    input=prompt,
                    max_output_tokens=max_output_tokens,
                    reasoning={"effort": "minimal"},
                    text={"verbosity": "low"}
                )
                
                # Track usage metrics
                llm_usage_collector.log_usage(
                    provider=LLMProvider.OPENAI,
                    model=model,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    operation_type=operation_type
                )
                
                return response.output_text
            
            return await loop.run_in_executor(None, _sync_request)
            
        except Exception as e:
            logger.error(f"Error making async LLM request ({operation_type}): {e}")
            raise

# Global instance to be used across the application  
llm_client = LLMClient()