"""Main workspace manager for Claude agents."""

import tempfile
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import json

from .file_handler import FileHandler
from .git_handler import GitHandler
from .mappings import (
    FileMapping, FolderMapping, GitRepoMapping,
    PathMapper
)

logger = logging.getLogger(__name__)


class WorkspaceManager:
    """Manages isolated workspaces for Claude agents."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize the workspace manager.
        
        Args:
            base_dir: Base directory for workspaces. If None, uses system temp.
        """
        self.base_dir = base_dir or Path(tempfile.gettempdir()) / "claude_workspaces"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.file_handler = FileHandler()
        self.git_handler = GitHandler()
        self.path_mapper = PathMapper()
        
        # Track active workspaces
        self.active_workspaces: Dict[str, Path] = {}
        
    def create_workspace(
        self,
        workspace_id: str,
        files: Optional[List[Dict[str, str]]] = None,
        folders: Optional[List[Dict[str, str]]] = None,
        repos: Optional[List[Dict[str, Any]]] = None,
        persistent: bool = False
    ) -> Path:
        """Create a new workspace with the specified resources.
        
        Args:
            workspace_id: Unique identifier for the workspace
            files: List of file mappings
            folders: List of folder mappings  
            repos: List of git repository mappings
            persistent: If True, workspace won't be auto-cleaned
            
        Returns:
            Path to the created workspace root
            
        Raises:
            ValueError: If workspace_id already exists
            RuntimeError: If workspace creation fails
        """
        if workspace_id in self.active_workspaces:
            raise ValueError(f"Workspace '{workspace_id}' already exists")
            
        # Create workspace directory
        if persistent:
            workspace_root = self.base_dir / f"persistent_{workspace_id}"
            workspace_root.mkdir(parents=True, exist_ok=True)
        else:
            workspace_root = Path(tempfile.mkdtemp(
                prefix=f"{workspace_id}_",
                dir=self.base_dir
            ))
            
        logger.info(f"Creating workspace: {workspace_root}")
        
        try:
            # Create workspace metadata
            metadata = {
                "workspace_id": workspace_id,
                "created_at": datetime.now().isoformat(),
                "persistent": persistent,
                "resources": {
                    "files": files or [],
                    "folders": folders or [],
                    "repos": repos or []
                }
            }
            
            # Write metadata
            metadata_file = workspace_root / ".workspace_metadata.json"
            metadata_file.write_text(json.dumps(metadata, indent=2))
            
            # Process file mappings
            if files:
                file_mappings = [
                    self.path_mapper.create_file_mapping(f) for f in files
                ]
                self.file_handler.copy_files(workspace_root, file_mappings)
                
            # Process folder mappings
            if folders:
                folder_mappings = [
                    self.path_mapper.create_folder_mapping(f) for f in folders
                ]
                self.file_handler.copy_folders(workspace_root, folder_mappings)
                
            # Process repository mappings
            if repos:
                if not self.git_handler.is_git_installed():
                    raise RuntimeError("Git is not installed or not in PATH")
                    
                repo_mappings = [
                    self.path_mapper.create_git_mapping(r) for r in repos
                ]
                self.git_handler.clone_repos(workspace_root, repo_mappings)
            
            # Track the workspace
            self.active_workspaces[workspace_id] = workspace_root
            
            logger.info(f"Workspace created successfully: {workspace_id}")
            return workspace_root
            
        except Exception as e:
            # Cleanup on failure
            logger.error(f"Failed to create workspace: {e}")
            if workspace_root.exists() and not persistent:
                shutil.rmtree(workspace_root, ignore_errors=True)
            raise
    
    def get_workspace(self, workspace_id: str) -> Optional[Path]:
        """Get the path to an active workspace.
        
        Args:
            workspace_id: The workspace identifier
            
        Returns:
            Path to the workspace or None if not found
        """
        return self.active_workspaces.get(workspace_id)
    
    def cleanup_workspace(self, workspace_id: str, force: bool = False) -> bool:
        """Clean up a workspace.
        
        Args:
            workspace_id: The workspace identifier
            force: If True, removes even persistent workspaces
            
        Returns:
            True if cleaned up, False if not found or persistent
        """
        workspace_path = self.active_workspaces.get(workspace_id)
        if not workspace_path:
            logger.warning(f"Workspace not found: {workspace_id}")
            return False
            
        # Check if persistent
        metadata_file = workspace_path / ".workspace_metadata.json"
        if metadata_file.exists():
            metadata = json.loads(metadata_file.read_text())
            if metadata.get("persistent") and not force:
                logger.info(f"Workspace is persistent, skipping cleanup: {workspace_id}")
                return False
        
        # Remove the workspace
        try:
            shutil.rmtree(workspace_path)
            del self.active_workspaces[workspace_id]
            logger.info(f"Cleaned up workspace: {workspace_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup workspace: {e}")
            return False
    
    def cleanup_all(self, force: bool = False) -> int:
        """Clean up all active workspaces.
        
        Args:
            force: If True, removes even persistent workspaces
            
        Returns:
            Number of workspaces cleaned up
        """
        workspace_ids = list(self.active_workspaces.keys())
        cleaned = 0
        
        for workspace_id in workspace_ids:
            if self.cleanup_workspace(workspace_id, force):
                cleaned += 1
                
        return cleaned
    
    def list_workspaces(self) -> Dict[str, Dict[str, Any]]:
        """List all active workspaces with their metadata.
        
        Returns:
            Dictionary of workspace_id -> workspace info
        """
        result = {}
        
        for workspace_id, path in self.active_workspaces.items():
            info = {
                "path": str(path),
                "exists": path.exists()
            }
            
            # Try to load metadata
            metadata_file = path / ".workspace_metadata.json"
            if metadata_file.exists():
                try:
                    metadata = json.loads(metadata_file.read_text())
                    info.update({
                        "created_at": metadata.get("created_at"),
                        "persistent": metadata.get("persistent", False),
                        "resources": metadata.get("resources", {})
                    })
                except Exception:
                    pass
                    
            result[workspace_id] = info
            
        return result
    
    def export_workspace(self, workspace_id: str, output_path: Path) -> Path:
        """Export a workspace as a tar archive.
        
        Args:
            workspace_id: The workspace identifier
            output_path: Path for the output archive
            
        Returns:
            Path to the created archive
            
        Raises:
            ValueError: If workspace not found
        """
        workspace_path = self.active_workspaces.get(workspace_id)
        if not workspace_path or not workspace_path.exists():
            raise ValueError(f"Workspace not found: {workspace_id}")
            
        # Create archive
        archive_path = shutil.make_archive(
            str(output_path.with_suffix("")),
            "tar",
            workspace_path
        )
        
        logger.info(f"Exported workspace to: {archive_path}")
        return Path(archive_path)