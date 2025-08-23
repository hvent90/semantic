"""Version control system interface for the Codebase Summarizer tool."""

import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any


logger = logging.getLogger(__name__)


class VcsInterface:
    """
    Interface to interact with version control systems (primarily Git).
    Retrieves metadata like commit hashes and handles graceful fallbacks.
    """
    
    def __init__(self, repository_path: Path):
        """
        Initialize the VCS interface for a specific repository.
        
        Args:
            repository_path: Path to the repository root or any directory within it
        """
        self.repository_path = Path(repository_path).resolve()
        
    def get_current_commit_hash(self) -> str:
        """
        Get the current commit hash from the repository.
        
        Returns:
            The full SHA commit hash, or 'UNCOMMITTED' if not available
        """
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.repository_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.debug(f"Git command failed: {result.stderr}")
                return 'UNCOMMITTED'
                
        except subprocess.TimeoutExpired:
            logger.warning("Git command timed out")
            return 'UNCOMMITTED'
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.debug("Git not available or not a git repository")
            return 'UNCOMMITTED'
            
    def get_short_commit_hash(self, length: int = 7) -> str:
        """
        Get a shortened version of the current commit hash.
        
        Args:
            length: Number of characters for the short hash
            
        Returns:
            The shortened commit hash, or 'UNCOMMIT' if not available
        """
        full_hash = self.get_current_commit_hash()
        if full_hash == 'UNCOMMITTED':
            return 'UNCOMMIT'
        return full_hash[:length]
        
    def is_git_repository(self) -> bool:
        """
        Check if the current path is within a Git repository.
        
        Returns:
            True if in a Git repository, False otherwise
        """
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.repository_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
            
    def has_uncommitted_changes(self) -> bool:
        """
        Check if there are uncommitted changes in the repository.
        
        Returns:
            True if there are uncommitted changes, False otherwise
        """
        try:
            # Check staged changes
            result_staged = subprocess.run(
                ['git', 'diff', '--cached', '--quiet'],
                cwd=self.repository_path,
                capture_output=True,
                timeout=10
            )
            
            # Check unstaged changes
            result_unstaged = subprocess.run(
                ['git', 'diff', '--quiet'],
                cwd=self.repository_path,
                capture_output=True,
                timeout=10
            )
            
            # If either command returns non-zero, there are changes
            return result_staged.returncode != 0 or result_unstaged.returncode != 0
            
        except (subprocess.SubprocessError, FileNotFoundError):
            # If git commands fail, assume there might be changes
            return True
            
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get comprehensive VCS metadata for the current repository state.
        
        Returns:
            Dictionary containing commit hash and repository status information
        """
        metadata = {}
        
        if self.is_git_repository():
            metadata['commit_hash'] = self.get_current_commit_hash()
            metadata['short_commit_hash'] = self.get_short_commit_hash()
            metadata['has_uncommitted_changes'] = self.has_uncommitted_changes()
            metadata['vcs_type'] = 'git'
        else:
            metadata['commit_hash'] = 'UNCOMMITTED'
            metadata['short_commit_hash'] = 'UNCOMMIT'
            metadata['has_uncommitted_changes'] = True
            metadata['vcs_type'] = None
            
        return metadata
        
    def get_branch_name(self) -> Optional[str]:
        """
        Get the current branch name.
        
        Returns:
            The branch name, or None if not available
        """
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=self.repository_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return None
                
        except (subprocess.SubprocessError, FileNotFoundError):
            return None