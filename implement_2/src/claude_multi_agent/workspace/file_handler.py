"""File and folder operations for workspace management."""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Optional

from .mappings import FileMapping, FolderMapping, PathMapper

logger = logging.getLogger(__name__)


class FileHandler:
    """Handles file and folder operations for workspaces."""
    
    def __init__(self):
        self.path_mapper = PathMapper()
        
    def copy_file(self, workspace_root: Path, mapping: FileMapping) -> Path:
        """Copy a single file to the workspace.
        
        Args:
            workspace_root: The workspace root directory
            mapping: File mapping information
            
        Returns:
            The destination path where the file was copied
            
        Raises:
            FileNotFoundError: If source file doesn't exist
            ValueError: If paths are invalid
        """
        # Validate the mapping
        mapping.validate()
        
        # Resolve destination path
        dest_dir = self.path_mapper.resolve_dest_path(workspace_root, mapping.dest_path)
        dest_file = dest_dir / mapping.name
        
        # Create destination directory if needed
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy the file
        src_path = Path(mapping.src_path)
        logger.info(f"Copying file: {src_path} -> {dest_file}")
        
        shutil.copy2(src_path, dest_file)
        
        # Verify the copy
        if not dest_file.exists():
            raise RuntimeError(f"Failed to copy file to {dest_file}")
            
        return dest_file
    
    def copy_folder(self, workspace_root: Path, mapping: FolderMapping) -> Path:
        """Copy a folder recursively to the workspace.
        
        Args:
            workspace_root: The workspace root directory
            mapping: Folder mapping information
            
        Returns:
            The destination path where the folder was copied
            
        Raises:
            FileNotFoundError: If source folder doesn't exist
            ValueError: If paths are invalid
        """
        # Validate the mapping
        mapping.validate()
        
        # Resolve destination path
        dest_path = self.path_mapper.resolve_dest_path(workspace_root, mapping.dest_path)
        dest_folder = dest_path / mapping.name
        
        # Remove existing folder if it exists
        if dest_folder.exists():
            logger.warning(f"Destination folder exists, removing: {dest_folder}")
            shutil.rmtree(dest_folder)
        
        # Copy the folder
        src_path = Path(mapping.src_path)
        logger.info(f"Copying folder: {src_path} -> {dest_folder}")
        
        shutil.copytree(src_path, dest_folder)
        
        # Verify the copy
        if not dest_folder.exists():
            raise RuntimeError(f"Failed to copy folder to {dest_folder}")
            
        return dest_folder
    
    def copy_files(self, workspace_root: Path, mappings: List[FileMapping]) -> List[Path]:
        """Copy multiple files to the workspace.
        
        Args:
            workspace_root: The workspace root directory
            mappings: List of file mappings
            
        Returns:
            List of destination paths where files were copied
        """
        results = []
        for mapping in mappings:
            try:
                dest = self.copy_file(workspace_root, mapping)
                results.append(dest)
            except Exception as e:
                logger.error(f"Failed to copy file {mapping.name}: {e}")
                raise
                
        return results
    
    def copy_folders(self, workspace_root: Path, mappings: List[FolderMapping]) -> List[Path]:
        """Copy multiple folders to the workspace.
        
        Args:
            workspace_root: The workspace root directory
            mappings: List of folder mappings
            
        Returns:
            List of destination paths where folders were copied
        """
        results = []
        for mapping in mappings:
            try:
                dest = self.copy_folder(workspace_root, mapping)
                results.append(dest)
            except Exception as e:
                logger.error(f"Failed to copy folder {mapping.name}: {e}")
                raise
                
        return results
    
    def create_directory(self, workspace_root: Path, rel_path: str) -> Path:
        """Create a directory within the workspace.
        
        Args:
            workspace_root: The workspace root directory
            rel_path: Relative path for the directory
            
        Returns:
            The created directory path
        """
        dir_path = self.path_mapper.resolve_dest_path(workspace_root, rel_path)
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")
        return dir_path
    
    def write_file(self, workspace_root: Path, rel_path: str, content: str) -> Path:
        """Write content to a file in the workspace.
        
        Args:
            workspace_root: The workspace root directory
            rel_path: Relative path for the file
            content: Content to write
            
        Returns:
            The file path
        """
        file_path = self.path_mapper.resolve_dest_path(workspace_root, rel_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_path.write_text(content)
        logger.info(f"Wrote file: {file_path}")
        return file_path