"""Configuration file handling for .semanticsrc files."""

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class SemanticConfig:
    """
    Handles loading and parsing of .semanticsrc configuration files.
    """
    
    def __init__(self, root_path: Path):
        """
        Initialize the configuration handler.
        
        Args:
            root_path: The root directory to look for .semanticsrc file
        """
        self.root_path = Path(root_path).resolve()
        self.config_path = self.root_path / ".semanticsrc"
        self._config_data = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from .semanticsrc file if it exists."""
        if not self.config_path.exists():
            logger.debug(f"No .semanticsrc file found at {self.config_path}")
            return
        
        if not HAS_YAML:
            logger.warning("PyYAML not installed. Cannot load .semanticsrc file. Install with: pip install PyYAML")
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config_data = yaml.safe_load(f) or {}
            logger.info(f"Loaded configuration from {self.config_path}")
        except yaml.YAMLError as e:
            logger.warning(f"Invalid YAML in {self.config_path}: {e}")
        except (IOError, UnicodeDecodeError) as e:
            logger.warning(f"Could not read {self.config_path}: {e}")
    
    def get_exclude_patterns(self) -> List[str]:
        """
        Get the list of exclude patterns from the configuration.
        
        Returns:
            List of glob patterns to exclude during traversal
        """
        patterns = self._config_data.get('exclude', [])
        if not isinstance(patterns, list):
            logger.warning("exclude patterns must be a list in .semanticsrc")
            return []
        
        # Ensure all patterns are strings
        string_patterns = []
        for pattern in patterns:
            if isinstance(pattern, str):
                string_patterns.append(pattern)
            else:
                logger.warning(f"Skipping non-string exclude pattern: {pattern}")
        
        logger.debug(f"Loaded {len(string_patterns)} exclude patterns")
        return string_patterns
    
    def should_exclude_path(self, path: Path) -> bool:
        """
        Check if a given path should be excluded based on configuration patterns.
        
        Args:
            path: The path to check
            
        Returns:
            True if the path should be excluded, False otherwise
        """
        exclude_patterns = self.get_exclude_patterns()
        if not exclude_patterns:
            return False
        
        # Convert path to relative path from root for pattern matching
        try:
            relative_path = path.relative_to(self.root_path)
        except ValueError:
            # Path is not relative to root, don't exclude
            return False
        
        path_str = str(relative_path)
        path_parts = relative_path.parts
        
        for pattern in exclude_patterns:
            # Handle directory patterns (ending with /)
            if pattern.endswith('/'):
                dir_pattern = pattern[:-1]
                # Check if any parent directory matches the pattern
                if dir_pattern in path_parts:
                    logger.debug(f"Excluding {path} (matches directory pattern: {pattern})")
                    return True
                # Check if the path itself matches as a directory
                if path.is_dir() and path.name == dir_pattern:
                    logger.debug(f"Excluding {path} (matches directory pattern: {pattern})")
                    return True
            else:
                # Handle file patterns and simple glob patterns
                import fnmatch
                if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(path.name, pattern):
                    logger.debug(f"Excluding {path} (matches pattern: {pattern})")
                    return True
        
        return False
    
    def get_output_format(self) -> str:
        """
        Get the output format from configuration.

        Returns:
            Output format string ('agents' or 'claude')
        """
        format_value = self._config_data.get('output_format', 'agents')
        valid_formats = {'agents', 'claude'}

        if format_value not in valid_formats:
            logger.warning(f"Invalid output_format '{format_value}' in .semanticsrc. Using 'agents'")
            return 'agents'

        return format_value

    def format_to_filename(self, format_type: str) -> str:
        """
        Convert format type to filename.

        Args:
            format_type: The format type ('agents' or 'claude')

        Returns:
            Corresponding filename
        """
        format_mapping = {
            'agents': 'agents.md',
            'claude': 'claude.md'
        }
        return format_mapping.get(format_type, 'agents.md')

    def has_config_file(self) -> bool:
        """
        Check if a .semanticsrc file exists.

        Returns:
            True if configuration file exists, False otherwise
        """
        return self.config_path.exists()
    
    def create_example_config(self) -> str:
        """
        Create an example .semanticsrc configuration.
        
        Returns:
            Example configuration as a YAML string
        """
        if HAS_YAML:
            example_config = {
                'output_format': 'agents',  # Options: agents, claude
                'exclude': [
                    'node_modules/',
                    '.venv/',
                    'venv/',
                    '*.log',
                    'dist/',
                    'build/',
                    '__pycache__/',
                    '.pytest_cache/',
                    '.git/',
                    '.DS_Store'
                ]
            }
            return yaml.dump(example_config, default_flow_style=False, sort_keys=False)
        else:
            # Fallback to manual YAML creation if PyYAML is not available
            return """# .semanticsrc Example
# Defines the output file format for generated summaries
output_format: agents  # Options: agents, claude

# Defines which directories/files to explicitly ignore during traversal.
exclude:
- node_modules/
- .venv/
- venv/
- '*.log'
- dist/
- build/
- __pycache__/
- .pytest_cache/
- .git/
- .DS_Store"""