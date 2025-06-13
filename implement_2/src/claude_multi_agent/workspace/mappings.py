"""Path mapping utilities and types for workspace management."""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re


@dataclass
class FileMapping:
    """Represents a file to be copied to the workspace."""
    name: str
    src_path: str
    dest_path: str
    
    def validate(self) -> None:
        """Validate the file mapping."""
        if not self.name:
            raise ValueError("File name cannot be empty")
            
        src = Path(self.src_path)
        if not src.exists():
            raise FileNotFoundError(f"Source file not found: {self.src_path}")
        if not src.is_file():
            raise ValueError(f"Source is not a file: {self.src_path}")
            
        # Validate dest_path doesn't try to escape workspace
        if ".." in self.dest_path or self.dest_path.startswith("/"):
            raise ValueError(f"Invalid destination path: {self.dest_path}")


@dataclass 
class FolderMapping:
    """Represents a folder to be copied to the workspace."""
    name: str
    src_path: str
    dest_path: str
    
    def validate(self) -> None:
        """Validate the folder mapping."""
        if not self.name:
            raise ValueError("Folder name cannot be empty")
            
        src = Path(self.src_path)
        if not src.exists():
            raise FileNotFoundError(f"Source folder not found: {self.src_path}")
        if not src.is_dir():
            raise ValueError(f"Source is not a folder: {self.src_path}")
            
        # Validate dest_path doesn't try to escape workspace
        if ".." in self.dest_path or self.dest_path.startswith("/"):
            raise ValueError(f"Invalid destination path: {self.dest_path}")


@dataclass
class GitRepoMapping:
    """Represents a git repository to be cloned to the workspace."""
    github: str  # Using 'github' to match the spec
    dest_path: str
    branch: Optional[str] = None
    shallow: bool = True  # Shallow clone by default for performance
    
    def validate(self) -> None:
        """Validate the git repository mapping."""
        if not self.github:
            raise ValueError("Repository URL cannot be empty")
            
        # Basic URL validation
        if not re.match(r'^https?://github\.com/[\w\-]+/[\w\-]+', self.github):
            raise ValueError(f"Invalid GitHub URL: {self.github}")
            
        # Validate dest_path doesn't try to escape workspace  
        if ".." in self.dest_path or self.dest_path.startswith("/"):
            raise ValueError(f"Invalid destination path: {self.dest_path}")


class PathMapper:
    """Utilities for safe path mapping within workspaces."""
    
    @staticmethod
    def resolve_dest_path(workspace_root: Path, dest_path: str) -> Path:
        """Safely resolve a destination path within the workspace.
        
        Args:
            workspace_root: The root directory of the workspace
            dest_path: The relative destination path
            
        Returns:
            The resolved absolute path
            
        Raises:
            ValueError: If the path would escape the workspace
        """
        # Normalize the path
        dest_path = os.path.normpath(dest_path)
        
        # Ensure it doesn't start with / or contain ..
        if dest_path.startswith("/") or ".." in dest_path:
            raise ValueError(f"Invalid destination path: {dest_path}")
            
        # Resolve the full path
        full_path = workspace_root / dest_path
        
        # Ensure it's still within the workspace (defense in depth)
        try:
            full_path.resolve().relative_to(workspace_root.resolve())
        except ValueError:
            raise ValueError(f"Path escapes workspace: {dest_path}")
            
        return full_path
    
    @staticmethod
    def create_file_mapping(mapping_dict: Dict[str, str]) -> FileMapping:
        """Create a FileMapping from a dictionary.
        
        Args:
            mapping_dict: Dictionary with keys: name, src_path, dest_path
            
        Returns:
            FileMapping instance
        """
        return FileMapping(
            name=mapping_dict["name"],
            src_path=mapping_dict["src_path"], 
            dest_path=mapping_dict["dest_path"]
        )
    
    @staticmethod
    def create_folder_mapping(mapping_dict: Dict[str, str]) -> FolderMapping:
        """Create a FolderMapping from a dictionary.
        
        Args:
            mapping_dict: Dictionary with keys: name, src_path, dest_path
            
        Returns:
            FolderMapping instance
        """
        return FolderMapping(
            name=mapping_dict["name"],
            src_path=mapping_dict["src_path"],
            dest_path=mapping_dict["dest_path"]
        )
    
    @staticmethod
    def create_git_mapping(mapping_dict: Dict[str, Any]) -> GitRepoMapping:
        """Create a GitRepoMapping from a dictionary.
        
        Args:
            mapping_dict: Dictionary with keys: github, dest_path, branch (optional)
            
        Returns:
            GitRepoMapping instance
        """
        return GitRepoMapping(
            github=mapping_dict["github"],
            dest_path=mapping_dict["dest_path"],
            branch=mapping_dict.get("branch"),
            shallow=mapping_dict.get("shallow", True)
        )