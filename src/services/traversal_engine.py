"""Directory traversal engine for the Codebase Summarizer tool."""

from pathlib import Path
from typing import List, Generator
import os


class TraversalEngine:
    """
    Implements depth-first traversal logic for codebase directory structures.
    Identifies directories to process and invokes analysis for each one.
    """
    
    def __init__(self, root_path: Path):
        """
        Initialize the traversal engine with a root directory path.
        
        Args:
            root_path: The root directory to start traversal from
        """
        self.root_path = Path(root_path).resolve()
        
    def should_skip_directory(self, directory: Path) -> bool:
        """
        Determine if a directory should be skipped during traversal.
        
        Args:
            directory: The directory path to check
            
        Returns:
            True if the directory should be skipped, False otherwise
        """
        skip_patterns = {
            '.git', '.hg', '.svn',  # Version control directories
            '__pycache__', '.pytest_cache',  # Python cache directories
            'node_modules',  # Node.js dependencies
            '.venv', 'venv', 'env',  # Virtual environments
            'dist', 'build',  # Build directories
            '.idea', '.vscode',  # IDE directories
            '.DS_Store'  # macOS system files
        }
        
        return directory.name in skip_patterns or directory.name.startswith('.')
        
    def get_directories_to_process(self) -> Generator[Path, None, None]:
        """
        Perform depth-first traversal and yield directories that should be processed.
        
        Yields:
            Path objects for directories that should have agents.md files generated
        """
        def _traverse(current_path: Path) -> Generator[Path, None, None]:
            if not current_path.is_dir() or self.should_skip_directory(current_path):
                return
                
            # Check if directory contains source files
            has_source_files = self._has_source_files(current_path)
            
            if has_source_files:
                yield current_path
                
            # Recursively traverse subdirectories
            try:
                for item in sorted(current_path.iterdir()):
                    if item.is_dir():
                        yield from _traverse(item)
            except (PermissionError, OSError):
                # Skip directories we can't access
                pass
                
        yield from _traverse(self.root_path)
        
    def _has_source_files(self, directory: Path) -> bool:
        """
        Check if a directory contains source code files.
        
        Args:
            directory: The directory to check
            
        Returns:
            True if the directory contains source files, False otherwise
        """
        source_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx',  # Python and JavaScript
            '.java', '.kt', '.scala',  # JVM languages
            '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp',  # C/C++
            '.rs',  # Rust
            '.go',  # Go
            '.rb',  # Ruby
            '.php',  # PHP
            '.cs',  # C#
            '.swift',  # Swift
            '.m', '.mm',  # Objective-C
            '.r', '.R',  # R
            '.sql',  # SQL
            '.sh', '.bash',  # Shell scripts
            '.ps1',  # PowerShell
            '.yaml', '.yml', '.json', '.toml', '.ini', '.cfg',  # Configuration
            '.md', '.rst',  # Documentation
        }
        
        try:
            for item in directory.iterdir():
                if item.is_file() and item.suffix.lower() in source_extensions:
                    return True
        except (PermissionError, OSError):
            pass
            
        return False
        
    def get_source_files_in_directory(self, directory: Path) -> List[Path]:
        """
        Get all source files in a specific directory (non-recursive).
        
        Args:
            directory: The directory to scan for source files
            
        Returns:
            List of Path objects for source files in the directory
        """
        source_files = []
        
        try:
            for item in sorted(directory.iterdir()):
                if item.is_file() and self._is_source_file(item):
                    source_files.append(item)
        except (PermissionError, OSError):
            pass
            
        return source_files
        
    def _is_source_file(self, file_path: Path) -> bool:
        """
        Check if a file is considered a source code file.
        
        Args:
            file_path: The file path to check
            
        Returns:
            True if the file is a source file, False otherwise
        """
        source_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx',
            '.java', '.kt', '.scala',
            '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp',
            '.rs', '.go', '.rb', '.php', '.cs', '.swift',
            '.m', '.mm', '.r', '.R', '.sql',
            '.sh', '.bash', '.ps1',
            '.yaml', '.yml', '.json', '.toml', '.ini', '.cfg',
            '.md', '.rst',
        }
        
        return file_path.suffix.lower() in source_extensions