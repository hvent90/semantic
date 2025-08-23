"""Analysis orchestrator for managing language parsers and aggregating results."""

import logging
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict

from models.data_models import DirectoryAnalysis, ApiInfo, AnalysisFragment
from parsers.language_parser_interface import LanguageParserInterface
from parsers.python_parser import PythonParser
from parsers.javascript_parser import JavaScriptParser
from services.llm_client import llm_client
from services.config import SemanticConfig


logger = logging.getLogger(__name__)


class AnalysisOrchestrator:
    """
    Orchestrates the analysis of a directory by managing different language parsers
    and aggregating their results into a comprehensive DirectoryAnalysis object.
    """
    
    def __init__(self):
        """Initialize the orchestrator with available language parsers."""
        self.parsers: List[LanguageParserInterface] = []
        self._register_default_parsers()
    
    def _register_default_parsers(self) -> None:
        """Register the default set of language parsers."""
        self.parsers.append(PythonParser())
        self.parsers.append(JavaScriptParser())
        logger.debug(f"Registered {len(self.parsers)} language parsers")
    
    def register_parser(self, parser: LanguageParserInterface) -> None:
        """
        Register a new language parser with the orchestrator.
        
        Args:
            parser: A language parser implementing LanguageParserInterface
        """
        self.parsers.append(parser)
        logger.debug(f"Registered parser: {type(parser).__name__}")
    
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
            
            # Find appropriate parser and analyze the file
            fragment = self._analyze_file(file_path)
            if fragment:
                analysis_fragments.append(fragment)
        
        # Aggregate results from all fragments, including comprehensive LLM analysis
        return self._aggregate_analysis_results(
            str(directory_path),
            analysis_fragments,
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
    
    def _analyze_file(self, file_path: Path) -> AnalysisFragment:
        """
        Analyze a single file using the appropriate parser.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            AnalysisFragment if parsing succeeded, None otherwise
        """
        # Find a parser that supports this file extension
        parser = self._find_parser_for_file(file_path)
        if not parser:
            logger.debug(f"No parser found for file: {file_path}")
            return None
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the file
            fragment = parser.parse(content, str(file_path))
            logger.debug(f"Successfully parsed {file_path} with {type(parser).__name__}")
            return fragment
            
        except (IOError, UnicodeDecodeError) as e:
            logger.warning(f"Could not read file {file_path}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error parsing {file_path} with {type(parser).__name__}: {e}")
            return None
    
    def _find_parser_for_file(self, file_path: Path) -> LanguageParserInterface:
        """
        Find the appropriate parser for a given file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Parser that supports the file, or None if none found
        """
        file_extension = file_path.suffix.lower()
        
        for parser in self.parsers:
            if parser.supports_extension(file_extension):
                return parser
        
        return None
    
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
        Get all file extensions supported by registered parsers.
        
        Returns:
            List of supported file extensions
        """
        extensions = set()
        for parser in self.parsers:
            extensions.update(parser.get_supported_extensions())
        return sorted(list(extensions))