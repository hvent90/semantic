"""Abstract base class for language parsers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from models.data_models import AnalysisFragment


class LanguageParserInterface(ABC):
    """
    Abstract base class defining the contract for language-specific parsers.
    
    This interface ensures modularity and extensibility as new language parsers
    are added to the system. Each parser must implement methods to determine
    file compatibility and extract analysis information.
    """
    
    @abstractmethod
    def supports_extension(self, ext: str) -> bool:
        """
        Determine if this parser can handle files with the given extension.
        
        Args:
            ext: File extension including the dot (e.g., '.py', '.js')
            
        Returns:
            True if this parser supports the extension, False otherwise
        """
        pass
    
    @abstractmethod
    def parse(self, file_content: str, file_path: str) -> AnalysisFragment:
        """
        Parse a source file and extract analysis information.
        
        Args:
            file_content: The raw content of the source file
            file_path: The path to the source file being analyzed
            
        Returns:
            AnalysisFragment containing APIs, skillsets, and metadata
            
        Raises:
            Exception: If parsing fails due to malformed syntax or other errors
        """
        pass
    
    def get_supported_extensions(self) -> List[str]:
        """
        Get a list of all file extensions supported by this parser.
        
        This is a convenience method that should be overridden by concrete
        implementations to return their supported extensions.
        
        Returns:
            List of supported file extensions (e.g., ['.py', '.pyi'])
        """
        return []
    
    def can_parse_file(self, file_path: Path) -> bool:
        """
        Convenience method to check if a file can be parsed by this parser.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if this parser can handle the file, False otherwise
        """
        return self.supports_extension(file_path.suffix.lower())