"""Git operations for workspace management."""

import subprocess
import logging
from pathlib import Path
from typing import List, Optional

from .mappings import GitRepoMapping, PathMapper

logger = logging.getLogger(__name__)


class GitHandler:
    """Handles git operations for workspaces."""
    
    def __init__(self):
        self.path_mapper = PathMapper()
        
    def clone_repo(self, workspace_root: Path, mapping: GitRepoMapping) -> Path:
        """Clone a git repository to the workspace.
        
        Args:
            workspace_root: The workspace root directory
            mapping: Git repository mapping information
            
        Returns:
            The destination path where the repo was cloned
            
        Raises:
            subprocess.CalledProcessError: If git clone fails
            ValueError: If paths are invalid
        """
        # Validate the mapping
        mapping.validate()
        
        # Resolve destination path
        dest_path = self.path_mapper.resolve_dest_path(workspace_root, mapping.dest_path)
        
        # Extract repo name from URL if dest_path is just a directory
        if mapping.dest_path == "." or mapping.dest_path == "":
            # Clone to root
            clone_target = workspace_root
        else:
            # Ensure parent directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            clone_target = dest_path
        
        # Build git command
        cmd = ["git", "clone"]
        
        if mapping.shallow:
            cmd.extend(["--depth", "1"])
            
        if mapping.branch:
            cmd.extend(["--branch", mapping.branch])
            
        cmd.extend([mapping.github, str(clone_target)])
        
        logger.info(f"Cloning repository: {mapping.github} -> {clone_target}")
        
        try:
            # Run git clone
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=workspace_root
            )
            
            logger.debug(f"Git clone output: {result.stdout}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git clone failed: {e.stderr}")
            raise RuntimeError(f"Failed to clone repository: {e.stderr}")
        
        # Verify the clone
        if not clone_target.exists():
            raise RuntimeError(f"Repository was not cloned to {clone_target}")
            
        # Check if it's a git repo (only if directory exists)
        if clone_target.exists():
            git_dir = clone_target / ".git"
            if not git_dir.exists():
                raise RuntimeError(f"Cloned directory is not a git repository: {clone_target}")
            
        return clone_target
    
    def clone_repos(self, workspace_root: Path, mappings: List[GitRepoMapping]) -> List[Path]:
        """Clone multiple repositories to the workspace.
        
        Args:
            workspace_root: The workspace root directory
            mappings: List of git repository mappings
            
        Returns:
            List of destination paths where repos were cloned
        """
        results = []
        for mapping in mappings:
            try:
                dest = self.clone_repo(workspace_root, mapping)
                results.append(dest)
            except Exception as e:
                logger.error(f"Failed to clone repo {mapping.github}: {e}")
                raise
                
        return results
    
    def is_git_installed(self) -> bool:
        """Check if git is installed and available.
        
        Returns:
            True if git is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            logger.debug(f"Git version: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def init_repo(self, workspace_root: Path) -> None:
        """Initialize a git repository in the workspace.
        
        Args:
            workspace_root: The workspace root directory
        """
        try:
            subprocess.run(
                ["git", "init"],
                capture_output=True,
                text=True,
                check=True,
                cwd=workspace_root
            )
            logger.info(f"Initialized git repository in {workspace_root}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Git init failed: {e.stderr}")
            raise RuntimeError(f"Failed to initialize git repository: {e.stderr}")