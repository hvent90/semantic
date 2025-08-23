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
            response_text = self._make_llm_request(
                prompt=prompt,
                max_output_tokens=500,
                operation_type="skillset_detection"
            )
            
            # Parse the response to extract skillset tags
            skillsets = self._parse_skillsets_response(response_text)
            logger.info(f"Generated skillsets for {directory_path}: {skillsets}")
            return skillsets
            
        except Exception as e:
            logger.error(f"Error generating skillsets: {e}")
            return []
    
    def get_context_window_size(self, model: str = "gpt-5-mini") -> int:
        """
        Get the context window size for the specified model.
        
        Args:
            model: The model name
            
        Returns:
            Context window size in tokens
        """
        # Known context windows for different models
        context_windows = {
            "gpt-3.5-turbo": 16385,
            "gpt-4": 8192,
            "gpt-4-turbo-preview": 128000,
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000,
            "gpt-5-nano": 400000,
            "gpt-5-mini": 400000,
            "gpt-5": 400000
        }
        return context_windows.get(model, 400000)
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text string.
        Uses a rough approximation of 4 characters per token.
        
        Args:
            text: The text to estimate tokens for
            
        Returns:
            Estimated number of tokens
        """
        return len(text) // 4
    
    def analyze_file_comprehensively(self, file_content: str, file_path: str) -> Tuple[List[ApiInfo], List[str]]:
        """
        Perform comprehensive analysis of a single file to extract both APIs and skillsets.
        
        Args:
            file_content: Complete content of the source file
            file_path: Path to the file being analyzed
            
        Returns:
            Tuple of (apis, skillsets) extracted from the file
        """
        if not self.is_available():
            logger.warning("LLM client not available, returning empty results")
            return [], []
        
        # Check if file content exceeds token limits
        file_tokens = self.estimate_tokens(file_content)
        context_window = self.get_context_window_size()
        threshold = int(context_window * 0.4)  # 40% of context window as per requirements
        
        if file_tokens > threshold:
            logger.info(f"File {file_path} exceeds token threshold ({file_tokens} > {threshold}), using chunking strategy")
            return self._analyze_large_file_comprehensively(file_content, file_path, threshold)
        else:
            logger.debug(f"Analyzing whole file {file_path} comprehensively ({file_tokens} tokens)")
            return self._analyze_single_file_comprehensively(file_content, file_path)
    
    def analyze_whole_file_for_apis(self, file_content: str, file_path: str) -> List[ApiInfo]:
        """
        Analyze an entire file to extract APIs using LLM.
        
        Args:
            file_content: Complete content of the source file
            file_path: Path to the file being analyzed
            
        Returns:
            List of ApiInfo objects with semantic descriptions
        """
        if not self.is_available():
            logger.warning("LLM client not available, returning empty API list")
            return []
        
        # Check if file content exceeds token limits
        file_tokens = self.estimate_tokens(file_content)
        context_window = self.get_context_window_size()
        threshold = int(context_window * 0.4)  # 40% of context window as per requirements
        
        if file_tokens > threshold:
            logger.info(f"File {file_path} exceeds token threshold ({file_tokens} > {threshold}), using chunking strategy")
            return self._analyze_large_file_with_chunks(file_content, file_path, threshold)
        else:
            logger.debug(f"Analyzing whole file {file_path} ({file_tokens} tokens)")
            return self._analyze_single_file(file_content, file_path)
    
    def _analyze_single_file(self, file_content: str, file_path: str) -> List[ApiInfo]:
        """
        Analyze a single file that fits within token limits.
        
        Args:
            file_content: Complete content of the source file
            file_path: Path to the file being analyzed
            
        Returns:
            List of ApiInfo objects
        """
        prompt = self._build_whole_file_api_analysis_prompt(file_content, file_path)
        
        try:
            response_text = self._make_llm_request(
                prompt=prompt,
                max_output_tokens=2000,
                operation_type="whole_file_api_analysis"
            )
            
            # Parse the JSON response
            apis = self._parse_api_analysis_response(response_text, file_path)
            logger.info(f"Extracted {len(apis)} APIs from {file_path}")
            return apis
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return []
    
    def _analyze_large_file_with_chunks(self, file_content: str, file_path: str, threshold: int) -> List[ApiInfo]:
        """
        Analyze a large file by splitting it into overlapping chunks.
        
        Args:
            file_content: Complete content of the source file
            file_path: Path to the file being analyzed
            threshold: Token threshold for chunking
            
        Returns:
            List of ApiInfo objects with duplicates removed
        """
        context_window = self.get_context_window_size()
        chunk_size = int(context_window * 0.35)  # 35% of context window per chunk
        overlap_size = int(context_window * 0.05)  # 5% overlap between chunks
        
        chunks = self._create_overlapping_chunks(file_content, chunk_size, overlap_size)
        logger.info(f"Split file {file_path} into {len(chunks)} chunks for analysis")
        
        all_apis = []
        chunk_number = 0
        
        # Process chunks concurrently would be ideal, but for now process sequentially
        for chunk in chunks:
            chunk_number += 1
            logger.debug(f"Processing chunk {chunk_number}/{len(chunks)} for {file_path}")
            
            chunk_apis = self._analyze_single_chunk(chunk, file_path, chunk_number)
            all_apis.extend(chunk_apis)
        
        # Remove duplicates based on API name and approximate line number
        deduplicated_apis = self._deduplicate_apis(all_apis)
        logger.info(f"After deduplication: {len(deduplicated_apis)} unique APIs from {len(all_apis)} total")
        
        return deduplicated_apis
    
    def _create_overlapping_chunks(self, content: str, chunk_size_tokens: int, overlap_size_tokens: int) -> List[str]:
        """
        Create overlapping chunks from file content.
        
        Args:
            content: The file content to chunk
            chunk_size_tokens: Maximum tokens per chunk
            overlap_size_tokens: Number of tokens to overlap between chunks
            
        Returns:
            List of content chunks
        """
        lines = content.split('\n')
        chunks = []
        
        # Convert token sizes to approximate character counts
        chunk_size_chars = chunk_size_tokens * 4
        overlap_size_chars = overlap_size_tokens * 4
        
        current_pos = 0
        
        while current_pos < len(content):
            # Calculate chunk boundaries
            chunk_end = min(current_pos + chunk_size_chars, len(content))
            chunk_text = content[current_pos:chunk_end]
            
            # Try to break at a reasonable line boundary
            if chunk_end < len(content):
                last_newline = chunk_text.rfind('\n')
                if last_newline > len(chunk_text) // 2:  # Only if we find a newline in the latter half
                    chunk_text = chunk_text[:last_newline]
                    chunk_end = current_pos + last_newline
            
            chunks.append(chunk_text)
            
            # Calculate next position with overlap
            if chunk_end >= len(content):
                break
                
            current_pos = chunk_end - overlap_size_chars
            if current_pos <= len(chunks[-1]) if chunks else False:
                current_pos = chunk_end  # Avoid infinite loop
        
        return chunks
    
    def _analyze_single_chunk(self, chunk_content: str, file_path: str, chunk_number: int) -> List[ApiInfo]:
        """
        Analyze a single chunk of a large file.
        
        Args:
            chunk_content: Content of the chunk
            file_path: Path to the original file
            chunk_number: Number of this chunk for logging
            
        Returns:
            List of ApiInfo objects from this chunk
        """
        prompt = self._build_chunk_api_analysis_prompt(chunk_content, file_path, chunk_number)
        
        try:
            response_text = self._make_llm_request(
                prompt=prompt,
                max_output_tokens=1500,
                operation_type="chunk_api_analysis"
            )
            
            # Parse the JSON response
            apis = self._parse_api_analysis_response(response_text, file_path)
            return apis
            
        except Exception as e:
            logger.error(f"Error analyzing chunk {chunk_number} of {file_path}: {e}")
            return []
    
    def _deduplicate_apis(self, apis: List[ApiInfo]) -> List[ApiInfo]:
        """
        Remove duplicate APIs based on name and approximate line number.
        
        Args:
            apis: List of potentially duplicate APIs
            
        Returns:
            List of unique APIs
        """
        seen_apis = {}
        unique_apis = []
        
        for api in apis:
            # Create a key based on name and approximate location
            key = f"{api.name}_{api.start_line // 10}"  # Group by 10-line blocks
            
            if key not in seen_apis:
                seen_apis[key] = api
                unique_apis.append(api)
            else:
                # Keep the API with the better description (longer, more detailed)
                existing_api = seen_apis[key]
                if len(api.semantic_description) > len(existing_api.semantic_description):
                    # Replace with better description
                    unique_apis = [a for a in unique_apis if a != existing_api]
                    unique_apis.append(api)
                    seen_apis[key] = api
        
        return unique_apis
    
    def _analyze_single_file_comprehensively(self, file_content: str, file_path: str) -> Tuple[List[ApiInfo], List[str]]:
        """
        Analyze a single file comprehensively that fits within token limits.
        
        Args:
            file_content: Complete content of the source file
            file_path: Path to the file being analyzed
            
        Returns:
            Tuple of (apis, skillsets)
        """
        prompt = self._build_comprehensive_analysis_prompt(file_content, file_path)
        
        try:
            response_text = self._make_llm_request(
                prompt=prompt,
                max_output_tokens=2500,
                operation_type="comprehensive_file_analysis"
            )
            
            # Parse the JSON response
            apis, skillsets = self._parse_comprehensive_analysis_response(response_text, file_path)
            logger.info(f"Comprehensive analysis of {file_path}: {len(apis)} APIs, {len(skillsets)} skillsets")
            return apis, skillsets
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis of {file_path}: {e}")
            return [], []
    
    def _analyze_large_file_comprehensively(self, file_content: str, file_path: str, threshold: int) -> Tuple[List[ApiInfo], List[str]]:
        """
        Analyze a large file comprehensively by splitting it into overlapping chunks.
        
        Args:
            file_content: Complete content of the source file
            file_path: Path to the file being analyzed
            threshold: Token threshold for chunking
            
        Returns:
            Tuple of (apis, skillsets) with duplicates removed
        """
        context_window = self.get_context_window_size()
        chunk_size = int(context_window * 0.35)  # 35% of context window per chunk
        overlap_size = int(context_window * 0.05)  # 5% overlap between chunks
        
        chunks = self._create_overlapping_chunks(file_content, chunk_size, overlap_size)
        logger.info(f"Split file {file_path} into {len(chunks)} chunks for comprehensive analysis")
        
        all_apis = []
        all_skillsets = []
        chunk_number = 0
        
        # Process chunks sequentially
        for chunk in chunks:
            chunk_number += 1
            logger.debug(f"Processing chunk {chunk_number}/{len(chunks)} comprehensively for {file_path}")
            
            chunk_apis, chunk_skillsets = self._analyze_single_chunk_comprehensively(chunk, file_path, chunk_number)
            all_apis.extend(chunk_apis)
            all_skillsets.extend(chunk_skillsets)
        
        # Remove duplicates
        deduplicated_apis = self._deduplicate_apis(all_apis)
        unique_skillsets = list(set(all_skillsets))  # Remove duplicate skillsets
        
        logger.info(f"After deduplication: {len(deduplicated_apis)} unique APIs, {len(unique_skillsets)} unique skillsets from {len(all_apis)} total APIs")
        
        return deduplicated_apis, unique_skillsets
    
    def _analyze_single_chunk_comprehensively(self, chunk_content: str, file_path: str, chunk_number: int) -> Tuple[List[ApiInfo], List[str]]:
        """
        Analyze a single chunk of a large file comprehensively.
        
        Args:
            chunk_content: Content of the chunk
            file_path: Path to the original file
            chunk_number: Number of this chunk for logging
            
        Returns:
            Tuple of (apis, skillsets) from this chunk
        """
        prompt = self._build_comprehensive_chunk_analysis_prompt(chunk_content, file_path, chunk_number)
        
        try:
            response_text = self._make_llm_request(
                prompt=prompt,
                max_output_tokens=2000,
                operation_type="comprehensive_chunk_analysis"
            )
            
            # Parse the JSON response
            apis, skillsets = self._parse_comprehensive_analysis_response(response_text, file_path)
            return apis, skillsets
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis of chunk {chunk_number} of {file_path}: {e}")
            return [], []
    
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
            response_text = self._make_llm_request(
                prompt=prompt,
                max_output_tokens=100,
                operation_type="api_description"
            )
            
            description = response_text.strip()
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
        return f"""You are an expert code analyzer that identifies technology skillsets from code.

Analyze the following code files from directory "{directory_path}" and identify the key technology skillsets required to work with this code.

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
        return f"""You are an expert code analyzer that writes concise, accurate descriptions of API functions.

Analyze this API function and write a single, concise sentence describing what it does.

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
    
    def _build_whole_file_api_analysis_prompt(self, file_content: str, file_path: str) -> str:
        """
        Build prompt for analyzing an entire file to extract APIs.
        
        Args:
            file_content: Complete file content
            file_path: Path to the file
            
        Returns:
            Prompt for LLM
        """
        return f"""You are an expert code analyzer that extracts API information from source files. Return valid JSON only.

Analyze this complete source file and extract all API definitions (functions, methods, classes, endpoints).

File: {file_path}

For each API found, provide:
1. name: The exact name/identifier
2. semantic_description: One concise sentence describing its purpose
3. start_line: Approximate line number where it starts (estimate from content)
4. end_line: Approximate line number where it ends (estimate from content)

Return ONLY a valid JSON array in this format:
[
  {{
    "name": "function_name",
    "semantic_description": "Brief description of what it does",
    "start_line": 10,
    "end_line": 25
  }}
]

File content:
{file_content}

JSON:"""
    
    def _build_chunk_api_analysis_prompt(self, chunk_content: str, file_path: str, chunk_number: int) -> str:
        """
        Build prompt for analyzing a chunk of a large file.
        
        Args:
            chunk_content: Content of the chunk
            file_path: Path to the original file
            chunk_number: Number of this chunk
            
        Returns:
            Prompt for LLM
        """
        return f"""You are an expert code analyzer that extracts API information from code chunks. Return valid JSON only.

Analyze this code chunk (part {chunk_number} of a larger file) and extract any API definitions.

Original file: {file_path}

Look for complete function/method/class definitions. Ignore incomplete definitions that are cut off.

Return ONLY a valid JSON array:
[
  {{
    "name": "api_name",
    "semantic_description": "Brief description",
    "start_line": 10,
    "end_line": 25
  }}
]

If no complete APIs found, return: []

Chunk content:
{chunk_content}

JSON:"""
    
    def _parse_api_analysis_response(self, response_text: str, file_path: str) -> List[ApiInfo]:
        """
        Parse LLM response containing API analysis results.
        
        Args:
            response_text: JSON response from LLM
            file_path: Path to the source file
            
        Returns:
            List of ApiInfo objects
        """
        if not response_text:
            return []
        
        try:
            # Clean up the response - sometimes LLM adds extra text
            response_text = response_text.strip()
            logger.debug(f"Raw LLM response for {file_path}: {response_text[:200]}..." if len(response_text) > 200 else f"Raw LLM response for {file_path}: {response_text}")
            
            # Find JSON array in the response
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            
            if start_idx == -1 or end_idx == 0:
                logger.warning(f"No valid JSON array found in response for {file_path}")
                logger.debug(f"Response text: {response_text}")
                return []
            
            json_str = response_text[start_idx:end_idx]
            logger.debug(f"Extracted JSON: {json_str}")
            api_data = json.loads(json_str)
            
            apis = []
            for item in api_data:
                if isinstance(item, dict) and all(key in item for key in ['name', 'semantic_description']):
                    api = ApiInfo(
                        name=str(item['name']),
                        semantic_description=str(item['semantic_description']),
                        source_file=file_path,
                        start_line=int(item.get('start_line', 1)),
                        end_line=int(item.get('end_line', 1))
                    )
                    apis.append(api)
                else:
                    logger.debug(f"Skipping invalid API item: {item}")
            
            logger.info(f"Successfully parsed {len(apis)} APIs from LLM response for {file_path}")
            return apis
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse API analysis response for {file_path}: {e}")
            logger.debug(f"Response text: {response_text}")
            return []
    
    def _build_comprehensive_analysis_prompt(self, file_content: str, file_path: str) -> str:
        """
        Build prompt for comprehensive analysis of an entire file to extract APIs and skillsets.
        
        Args:
            file_content: Complete file content
            file_path: Path to the file
            
        Returns:
            Prompt for LLM
        """
        return f"""You are an expert code analyzer. Analyze this complete source file and extract both API information and technology skillsets. Return valid JSON only.

File: {file_path}

Extract:
1. APIs: All function/method/class definitions with their descriptions
2. Skillsets: Technology skills and frameworks used in this file

Return ONLY a valid JSON object in this exact format:
{{
  "apis": [
    {{
      "name": "function_name",
      "semantic_description": "Brief description of what it does",
      "start_line": 10,
      "end_line": 25
    }}
  ],
  "skillsets": ["Python", "FastAPI", "SQLAlchemy"]
}}

File content:
{file_content}

JSON:"""
    
    def _build_comprehensive_chunk_analysis_prompt(self, chunk_content: str, file_path: str, chunk_number: int) -> str:
        """
        Build prompt for comprehensive analysis of a chunk of a large file.
        
        Args:
            chunk_content: Content of the chunk
            file_path: Path to the original file
            chunk_number: Number of this chunk
            
        Returns:
            Prompt for LLM
        """
        return f"""You are an expert code analyzer. Analyze this code chunk (part {chunk_number} of a larger file) and extract both API information and technology skillsets. Return valid JSON only.

Original file: {file_path}

Look for:
1. Complete function/method/class definitions (ignore incomplete/cut-off definitions)
2. Technology skills and frameworks used in this chunk

Return ONLY a valid JSON object:
{{
  "apis": [
    {{
      "name": "api_name",
      "semantic_description": "Brief description",
      "start_line": 10,
      "end_line": 25
    }}
  ],
  "skillsets": ["Technology1", "Framework2"]
}}

If no complete APIs found, use: "apis": []
If no skillsets found, use: "skillsets": []

Chunk content:
{chunk_content}

JSON:"""
    
    def _parse_comprehensive_analysis_response(self, response_text: str, file_path: str) -> Tuple[List[ApiInfo], List[str]]:
        """
        Parse LLM response containing comprehensive analysis results (APIs + skillsets).
        
        Args:
            response_text: JSON response from LLM
            file_path: Path to the source file
            
        Returns:
            Tuple of (apis, skillsets)
        """
        if not response_text:
            return [], []
        
        try:
            # Clean up the response - sometimes LLM adds extra text
            response_text = response_text.strip()
            logger.debug(f"Raw comprehensive LLM response for {file_path}: {response_text[:200]}..." if len(response_text) > 200 else f"Raw comprehensive LLM response for {file_path}: {response_text}")
            
            # Find JSON object in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                logger.warning(f"No valid JSON object found in comprehensive response for {file_path}")
                logger.debug(f"Response text: {response_text}")
                return [], []
            
            json_str = response_text[start_idx:end_idx]
            logger.debug(f"Extracted JSON: {json_str}")
            data = json.loads(json_str)
            
            # Parse APIs
            apis = []
            if 'apis' in data and isinstance(data['apis'], list):
                for item in data['apis']:
                    if isinstance(item, dict) and all(key in item for key in ['name', 'semantic_description']):
                        api = ApiInfo(
                            name=str(item['name']),
                            semantic_description=str(item['semantic_description']),
                            source_file=file_path,
                            start_line=int(item.get('start_line', 1)),
                            end_line=int(item.get('end_line', 1))
                        )
                        apis.append(api)
                    else:
                        logger.debug(f"Skipping invalid API item: {item}")
            
            # Parse skillsets
            skillsets = []
            if 'skillsets' in data and isinstance(data['skillsets'], list):
                skillsets = [str(skill) for skill in data['skillsets'] if isinstance(skill, str) and 2 <= len(str(skill)) <= 50]
            
            logger.info(f"Successfully parsed comprehensive analysis for {file_path}: {len(apis)} APIs, {len(skillsets)} skillsets")
            return apis, skillsets
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse comprehensive analysis response for {file_path}: {e}")
            logger.debug(f"Response text: {response_text}")
            return [], []
    
    def generate_semantic_file_content(self, directory_analysis: DirectoryAnalysis, directory_path: str, commit_hash: str = "UNCOMMITTED") -> str:
        """
        Generate the complete content of a .semantic (agents.md) file using LLM.
        
        Args:
            directory_analysis: Analysis results for the directory
            directory_path: Path to the directory being analyzed
            commit_hash: Git commit hash or placeholder
            
        Returns:
            Complete .semantic file content as markdown string
        """
        if not self.is_available():
            logger.warning("LLM client not available, generating basic semantic file content")
            return self._generate_basic_semantic_content(directory_analysis, directory_path, commit_hash)
        
        prompt = self._build_semantic_file_generation_prompt(directory_analysis, directory_path, commit_hash)
        
        try:
            response_text = self._make_llm_request(
                prompt=prompt,
                max_output_tokens=3000,
                operation_type="semantic_file_generation"
            )
            
            logger.info(f"Generated semantic file content for {directory_path}")
            return response_text.strip()
            
        except Exception as e:
            logger.error(f"Error generating semantic file content for {directory_path}: {e}")
            return self._generate_basic_semantic_content(directory_analysis, directory_path, commit_hash)
    
    def _build_semantic_file_generation_prompt(self, directory_analysis: DirectoryAnalysis, directory_path: str, commit_hash: str) -> str:
        """
        Build prompt for generating semantic file content based on directory analysis.
        
        Args:
            directory_analysis: Analysis results for the directory
            directory_path: Path to the directory
            commit_hash: Git commit hash
            
        Returns:
            Prompt for LLM
        """
        # Format APIs by file for better organization
        apis_by_file = {}
        for api in directory_analysis.apis:
            file_name = api.source_file.split('/')[-1] if '/' in api.source_file else api.source_file
            if file_name not in apis_by_file:
                apis_by_file[file_name] = []
            apis_by_file[file_name].append(api)
        
        # Build file types summary
        file_types_text = "\n".join([f"- {ext}: {count}" for ext, count in directory_analysis.file_types.items()])
        
        # Build skillsets summary
        skillsets_text = "\n".join([f"- {skill}" for skill in directory_analysis.required_skillsets])
        
        # Build APIs summary
        apis_text = ""
        for file_name, file_apis in apis_by_file.items():
            apis_text += f"### `{file_name}`\n"
            for api in file_apis:
                apis_text += f"- **{api.name}** (lines {api.start_line}-{api.end_line}): {api.semantic_description}\n"
        
        return f"""You are an expert technical documentation generator that creates semantic summary files for AI coding agents.

Your role is to generate a structured overview of a codebase file for AI agents to understand and navigate effectively.

Here is an example of the expected format:

```markdown
## Required Skillsets
- Python
- FastAPI
- SQL

## APIs
### `user_service.py`
class Authenticator (lines 10-100): Handles user authentication and authorization. 
  - (lines 25-45) public getUserById(id: number) -> User: Fetches a user record from the database by their primary ID.
  - (lines 58-70) public deleteUser(id: number) -> bool: Removes a user record from the database.
```

Requirements: Format APIs grouped by source file with proper markdown formatting

Now generate the complete file content for the below files:



Generate the complete overview now:"""
    
    def _generate_basic_semantic_content(self, directory_analysis: DirectoryAnalysis, directory_path: str, commit_hash: str) -> str:
        """
        Generate basic semantic file content without LLM (fallback).
        
        Args:
            directory_analysis: Analysis results for the directory
            directory_path: Path to the directory
            commit_hash: Git commit hash
            
        Returns:
            Basic .semantic file content
        """
        from datetime import datetime
        
        # Calculate line numbers for TOC
        header_lines = 4  # TABLE-OF-CONTENTS line + blank + [TOC] + first entry
        metadata_lines = 3  # section header + 2 metadata entries
        file_types_lines = 1 + len(directory_analysis.file_types)  # header + entries
        skillsets_lines = 1 + len(directory_analysis.required_skillsets)  # header + entries
        
        # Count API lines
        apis_by_file = {}
        for api in directory_analysis.apis:
            file_name = api.source_file.split('/')[-1] if '/' in api.source_file else api.source_file
            if file_name not in apis_by_file:
                apis_by_file[file_name] = []
            apis_by_file[file_name].append(api)
        
        apis_lines = 1  # section header
        for file_name, file_apis in apis_by_file.items():
            apis_lines += 1 + len(file_apis)  # file header + API entries
        
        toc_lines = 4  # [TOC], 4 entries, [/TOC]
        
        # Calculate section start lines
        metadata_start = header_lines + toc_lines + 2
        metadata_end = metadata_start + metadata_lines - 1
        
        file_types_start = metadata_end + 2
        file_types_end = file_types_start + file_types_lines - 1
        
        skillsets_start = file_types_end + 2
        skillsets_end = skillsets_start + skillsets_lines - 1
        
        apis_start = skillsets_end + 2
        apis_end = apis_start + apis_lines - 1
        
        # Generate content
        content = f"""TABLE-OF-CONTENTS: lines 4-{3 + toc_lines}

[TOC]
- Metadata: {metadata_start}-{metadata_end}
- File Types: {file_types_start}-{file_types_end}
- Required Skillsets: {skillsets_start}-{skillsets_end}
- APIs: {apis_start}-{apis_end}
[/TOC]

## Metadata
- last_generated_utc: {datetime.utcnow().isoformat()}Z
- commit_hash: {commit_hash}

## File Types
"""
        
        # Add file types
        for ext, count in directory_analysis.file_types.items():
            content += f"- {ext}: {count}\n"
        
        content += "\n## Required Skillsets\n"
        
        # Add skillsets
        for skill in directory_analysis.required_skillsets:
            content += f"- {skill}\n"
        
        content += "\n## APIs\n"
        
        # Add APIs grouped by file
        for file_name, file_apis in apis_by_file.items():
            content += f"### `{file_name}`\n"
            for api in file_apis:
                content += f"- **{api.name}** (lines {api.start_line}-{api.end_line}): {api.semantic_description}\n"
        
        return content


# Global instance to be used across the application  
llm_client = LLMClient()