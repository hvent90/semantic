"""LLM client service for generating skillsets and API descriptions."""

import os
import logging
from typing import List, Optional
from openai import OpenAI
from pathlib import Path

from services.llm_usage_metrics import LLMProvider, llm_usage_collector


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
    
    def generate_skillsets(self, file_contents: List[str], directory_path: str) -> List[str]:
        """
        Generate required skillsets based on file contents in a directory.
        
        Args:
            file_contents: List of file contents to analyze
            directory_path: Path to the directory being analyzed
            
        Returns:
            List of skillset tags (e.g., ['React', 'Django', 'API-Design'])
        """
        if not self.is_available():
            logger.warning("LLM client not available, returning empty skillsets")
            return []
        
        # Combine file contents with size limit
        combined_content = self._combine_file_contents(file_contents, max_tokens=8000)
        
        prompt = self._build_skillsets_prompt(combined_content, directory_path)
        
        try:
            response = self._client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert code analyzer that identifies technology skillsets from code."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            # Track usage metrics
            llm_usage_collector.log_usage(
                provider=LLMProvider.OPENAI,
                model="gpt-3.5-turbo",
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                operation_type="skillset_detection"
            )
            
            # Parse the response to extract skillset tags
            skillsets = self._parse_skillsets_response(response.choices[0].message.content)
            logger.info(f"Generated skillsets for {directory_path}: {skillsets}")
            return skillsets
            
        except Exception as e:
            logger.error(f"Error generating skillsets: {e}")
            return []
    
    def generate_api_description(self, api_code: str, api_name: str, source_file: str) -> str:
        """
        Generate a semantic description for an API function/method.
        
        Args:
            api_code: The code of the API function/method
            api_name: The name of the API
            source_file: The source file containing the API
            
        Returns:
            Concise one-sentence description of the API's function
        """
        if not self.is_available():
            logger.warning("LLM client not available, returning generic description")
            return f"Function {api_name} in {source_file}"
        
        prompt = self._build_api_description_prompt(api_code, api_name, source_file)
        
        try:
            response = self._client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert code analyzer that writes concise, accurate descriptions of API functions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.2
            )
            
            # Track usage metrics
            llm_usage_collector.log_usage(
                provider=LLMProvider.OPENAI,
                model="gpt-3.5-turbo",
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                operation_type="api_description"
            )
            
            description = response.choices[0].message.content.strip()
            # Ensure it's a single sentence and not too long
            if len(description) > 200:
                description = description[:197] + "..."
            
            logger.debug(f"Generated description for {api_name}: {description}")
            return description
            
        except Exception as e:
            logger.error(f"Error generating API description for {api_name}: {e}")
            return f"Function {api_name} in {source_file}"
    
    def _combine_file_contents(self, file_contents: List[str], max_tokens: int = 8000) -> str:
        """
        Combine file contents with a reasonable token limit.
        
        Args:
            file_contents: List of file contents
            max_tokens: Approximate maximum tokens (rough estimate: 4 chars = 1 token)
            
        Returns:
            Combined and truncated content
        """
        max_chars = max_tokens * 4  # Rough approximation
        combined = ""
        
        for content in file_contents:
            if len(combined) + len(content) + 100 < max_chars:  # Leave some buffer
                combined += f"\n--- File Content ---\n{content}\n"
            else:
                # Truncate the last file if needed
                remaining_space = max_chars - len(combined) - 100
                if remaining_space > 500:  # Only add if we have reasonable space
                    combined += f"\n--- File Content (truncated) ---\n{content[:remaining_space]}\n"
                break
        
        return combined
    
    def _build_skillsets_prompt(self, file_contents: str, directory_path: str) -> str:
        """Build the prompt for skillset detection."""
        return f"""Analyze the following code files from directory "{directory_path}" and identify the key technology skillsets required to work with this code.

Focus on:
- Programming languages and frameworks
- Libraries and dependencies used
- Architecture patterns (e.g., REST API, MVC, microservices)
- Development methodologies and tools

Return ONLY a comma-separated list of skillset tags (e.g., "Python, FastAPI, SQLAlchemy, REST API, pytest").
Be specific but concise. Limit to 8 most important skillsets.

Code files:
{file_contents}

Skillsets:"""
    
    def _build_api_description_prompt(self, api_code: str, api_name: str, source_file: str) -> str:
        """Build the prompt for API description generation."""
        return f"""Analyze this API function and write a single, concise sentence describing what it does.

Function name: {api_name}
Source file: {source_file}

Code:
{api_code}

Write exactly one sentence that clearly explains the function's purpose and behavior. Start with an active verb. Do not include implementation details.

Description:"""
    
    def _parse_skillsets_response(self, response_text: str) -> List[str]:
        """
        Parse the LLM response to extract skillset tags.
        
        Args:
            response_text: Raw response from LLM
            
        Returns:
            List of cleaned skillset tags
        """
        if not response_text:
            return []
        
        # Split by comma and clean up
        skillsets = [tag.strip() for tag in response_text.split(",")]
        
        # Filter out empty or very short tags, and limit length
        cleaned_skillsets = []
        for skillset in skillsets:
            # Remove quotes and extra whitespace
            skillset = skillset.strip().strip('"').strip("'").strip()
            
            # Skip empty, very short, or very long tags
            if 2 <= len(skillset) <= 50:
                cleaned_skillsets.append(skillset)
        
        # Limit to reasonable number
        return cleaned_skillsets[:10]


# Global instance to be used across the application  
llm_client = LLMClient()