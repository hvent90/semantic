"""Analysis orchestrator for managing language parsers and aggregating results."""

import logging
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict

from models.data_models import DirectoryAnalysis, ApiInfo, AnalysisFragment
from services.llm_client import llm_client
from services.config import SemanticConfig


logger = logging.getLogger(__name__)


class AnalysisOrchestrator:
    """
    Orchestrates the analysis of a directory using LLM-based analysis
    and aggregating results into a comprehensive DirectoryAnalysis object.
    """

    def __init__(self):
        """Initialize the orchestrator for LLM-based analysis."""
        logger.debug("Initialized AnalysisOrchestrator with LLM-based analysis")
    
    def analyze_directory(self, directory_path: Path) -> DirectoryAnalysis:
        """
        Analyze all source files in a directory and aggregate results.
        
        Args:
            directory_path: Path to the directory to analyze
            
        Returns:
            DirectoryAnalysis containing aggregated results from all files
        """
        logger.info(f"Analyzing directory: {directory_path}")
        
        # Create config object for file-level exclusions
        config = SemanticConfig(directory_path.parent if directory_path.parent.exists() else directory_path)
        
        # Get all source files in the directory (non-recursive)
        source_files = self._get_source_files(directory_path, config)
        logger.debug(f"Found {len(source_files)} source files")
        
        # Analyze each file with comprehensive LLM analysis (single request per file)
        analysis_fragments = []
        file_type_counts = defaultdict(int)
        all_llm_apis = []  # Store APIs from comprehensive LLM analysis
        all_llm_skillsets = []  # Store skillsets from comprehensive LLM analysis
        
        for file_path in source_files:
            # Count file types
            file_extension = file_path.suffix.lower()
            file_type_counts[file_extension] += 1
            
            # Read file content for comprehensive LLM analysis
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Use LLM for comprehensive file analysis (APIs + skillsets in one request)
                    if llm_client.is_available():
                        logger.debug(f"Performing comprehensive analysis for {file_path}")
                        llm_apis, llm_skillsets = llm_client.analyze_file_comprehensively(content, str(file_path))
                        
                        if llm_apis:
                            all_llm_apis.extend(llm_apis)
                            logger.info(f"✓ LLM extracted {len(llm_apis)} APIs from {file_path}")
                        else:
                            logger.warning(f"⚠ LLM returned 0 APIs from {file_path}")
                            
                        if llm_skillsets:
                            all_llm_skillsets.extend(llm_skillsets)
                            logger.info(f"✓ LLM extracted {len(llm_skillsets)} skillsets from {file_path}")
            except (IOError, UnicodeDecodeError) as e:
                logger.debug(f"Could not read file for analysis {file_path}: {e}")
            
            # Note: Parser-based analysis removed - using LLM analysis only
        
        # Aggregate results from LLM analysis only (parsers removed)
        return self._aggregate_analysis_results(
            str(directory_path),
            [],  # No parser fragments since parsers are removed
            dict(file_type_counts),
            all_llm_skillsets,  # Now comes from comprehensive per-file analysis
            all_llm_apis
        )
    
    def _get_source_files(self, directory_path: Path, config: SemanticConfig = None) -> List[Path]:
        """
        Get all source files in the directory, respecting exclusion patterns.
        
        Args:
            directory_path: Path to scan for source files
            config: Optional configuration object for exclusions
            
        Returns:
            List of source file paths
        """
        source_files = []
        
        # Define source file extensions (comprehensive list)
        source_extensions = {
            '.py', '.pyi',  # Python
            '.js', '.jsx', '.ts', '.tsx', '.mjs',  # JavaScript/TypeScript
            '.java', '.kt', '.scala',  # JVM languages
            '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx',  # C/C++
            '.rs',  # Rust
            '.go',  # Go
            '.rb',  # Ruby
            '.php',  # PHP
            '.cs',  # C#
            '.swift',  # Swift
            '.m', '.mm',  # Objective-C
            '.r', '.R',  # R
            '.sql',  # SQL
            '.sh', '.bash', '.zsh',  # Shell scripts
            '.ps1',  # PowerShell
            '.yaml', '.yml',  # YAML
            '.json',  # JSON
            '.toml',  # TOML
            '.ini', '.cfg', '.conf',  # Configuration files
            '.md', '.rst',  # Documentation
        }
        
        try:
            for item in directory_path.iterdir():
                if (item.is_file() and 
                    item.suffix.lower() in source_extensions and
                    not item.name.startswith('.')):  # Skip hidden files
                    
                    # Check configuration-based exclusions if config is available
                    if config and config.should_exclude_path(item):
                        logger.debug(f"Excluding file {item} due to configuration")
                        continue
                        
                    source_files.append(item)
        except (PermissionError, OSError) as e:
            logger.warning(f"Could not access directory {directory_path}: {e}")
        
        return sorted(source_files)
    

    
    def _aggregate_analysis_results(
        self,
        directory_path: str,
        fragments: List[AnalysisFragment],
        file_type_counts: Dict[str, int],
        llm_skillsets: List[str] = None,
        llm_apis: List[ApiInfo] = None
    ) -> DirectoryAnalysis:
        """
        Aggregate analysis fragments into a single DirectoryAnalysis.
        
        Args:
            directory_path: Path to the analyzed directory
            fragments: List of analysis fragments from individual files
            file_type_counts: Dictionary mapping file extensions to counts
            llm_skillsets: Optional list of skillsets from LLM analysis
            llm_apis: Optional list of APIs from whole-file LLM analysis
            
        Returns:
            Aggregated DirectoryAnalysis object
        """
        all_apis = []
        skillset_set: Set[str] = set()
        
        # Prioritize LLM APIs if available, fallback to parser APIs
        if llm_apis:
            logger.info(f"✓ Using LLM-extracted APIs: {len(llm_apis)} APIs found")
            all_apis.extend(llm_apis)
            
            # Still collect skillsets from fragments for technology detection
            for fragment in fragments:
                skillset_set.update(fragment.skillsets)
        else:
            logger.warning(f"⚠ LLM APIs empty or None (llm_apis={llm_apis}), using parser-extracted APIs as fallback")
            # Aggregate data from all fragments (fallback behavior)
            for fragment in fragments:
                all_apis.extend(fragment.apis)
                skillset_set.update(fragment.skillsets)
        
        # Add LLM-generated skillsets if available
        if llm_skillsets:
            skillset_set.update(llm_skillsets)
            logger.debug(f"Added LLM skillsets: {llm_skillsets}")
        
        # Sort APIs by source file and line number for consistent output
        all_apis.sort(key=lambda api: (api.source_file, api.start_line))
        
        # Convert skillsets to sorted list
        required_skillsets = sorted(list(skillset_set))
        
        logger.info(
            f"Aggregated results: {len(all_apis)} APIs, "
            f"{len(required_skillsets)} skillsets, "
            f"{sum(file_type_counts.values())} files"
        )
        
        return DirectoryAnalysis(
            directory_path=directory_path,
            file_types=file_type_counts,
            required_skillsets=required_skillsets,
            apis=all_apis
        )
    
    def get_supported_extensions(self) -> List[str]:
        """
        Get all file extensions supported by the analysis system.
        Since parsers are removed, this returns a comprehensive list of common source file extensions.

        Returns:
            List of supported file extensions
        """
        return [
            '.py', '.pyi',  # Python
            '.js', '.jsx', '.ts', '.tsx', '.mjs',  # JavaScript/TypeScript
            '.java', '.kt', '.scala',  # JVM languages
            '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx',  # C/C++
            '.rs',  # Rust
            '.go',  # Go
            '.rb',  # Ruby
            '.php',  # PHP
            '.cs',  # C#
            '.swift',  # Swift
            '.m', '.mm',  # Objective-C
            '.r', '.R',  # R
            '.sql',  # SQL
            '.sh', '.bash', '.zsh',  # Shell scripts
            '.ps1',  # PowerShell
            '.yaml', '.yml',  # YAML
            '.json',  # JSON
            '.toml',  # TOML
            '.ini', '.cfg', '.conf',  # Configuration files
            '.md', '.rst',  # Documentation
        ]