"""Tests for the main workspace manager."""

import pytest
from pathlib import Path
import json
import tempfile
from unittest.mock import patch, MagicMock

from claude_multi_agent.workspace.manager import WorkspaceManager


class TestWorkspaceManager:
    """Test WorkspaceManager functionality."""
    
    @pytest.fixture
    def manager(self, tmp_path):
        """Create a WorkspaceManager with temp base directory."""
        return WorkspaceManager(base_dir=tmp_path / "workspaces")
        
    @pytest.fixture
    def sample_files(self, tmp_path):
        """Create sample files for testing."""
        files_dir = tmp_path / "sample_files"
        files_dir.mkdir()
        
        # Create test files
        (files_dir / "config.json").write_text('{"setting": "value"}')
        (files_dir / "script.py").write_text('print("Hello")')
        
        return [
            {
                "name": "config.json",
                "src_path": str(files_dir / "config.json"),
                "dest_path": "config"
            },
            {
                "name": "script.py",
                "src_path": str(files_dir / "script.py"),
                "dest_path": "src"
            }
        ]
        
    @pytest.fixture
    def sample_folders(self, tmp_path):
        """Create sample folders for testing."""
        folders_dir = tmp_path / "sample_folders"
        folders_dir.mkdir()
        
        # Create test folder structure
        data_dir = folders_dir / "data"
        data_dir.mkdir()
        (data_dir / "file1.txt").write_text("Data 1")
        (data_dir / "file2.txt").write_text("Data 2")
        
        return [
            {
                "name": "data",
                "src_path": str(data_dir),
                "dest_path": "resources"
            }
        ]
        
    def test_create_empty_workspace(self, manager):
        """Test creating an empty workspace."""
        workspace_path = manager.create_workspace("test-workspace")
        
        assert workspace_path.exists()
        assert workspace_path.is_dir()
        assert "test-workspace" in manager.active_workspaces
        
        # Check metadata
        metadata_file = workspace_path / ".workspace_metadata.json"
        assert metadata_file.exists()
        
        metadata = json.loads(metadata_file.read_text())
        assert metadata["workspace_id"] == "test-workspace"
        assert metadata["persistent"] is False
        
    def test_create_workspace_with_files(self, manager, sample_files):
        """Test creating workspace with files."""
        workspace_path = manager.create_workspace(
            "file-workspace",
            files=sample_files
        )
        
        # Verify files were copied
        assert (workspace_path / "config" / "config.json").exists()
        assert (workspace_path / "src" / "script.py").exists()
        
        # Verify content
        config_content = (workspace_path / "config" / "config.json").read_text()
        assert '"setting": "value"' in config_content
        
    def test_create_workspace_with_folders(self, manager, sample_folders):
        """Test creating workspace with folders."""
        workspace_path = manager.create_workspace(
            "folder-workspace",
            folders=sample_folders
        )
        
        # Verify folder structure
        data_path = workspace_path / "resources" / "data"
        assert data_path.exists()
        assert (data_path / "file1.txt").exists()
        assert (data_path / "file2.txt").exists()
        
    @patch("claude_multi_agent.workspace.git_handler.subprocess.run")
    def test_create_workspace_with_repos(self, mock_run, manager):
        """Test creating workspace with git repositories."""
        # We need to mock both the git command and create the expected directory
        def mock_git_clone(*args, **kwargs):
            # Extract the target directory from the command
            cmd = args[0] if args else kwargs.get('args', [])
            if cmd and "clone" in cmd:
                # Last argument is the target directory
                target_dir = Path(cmd[-1])
                target_dir.mkdir(parents=True, exist_ok=True)
                (target_dir / ".git").mkdir(exist_ok=True)
            
            return MagicMock(
                stdout="Cloning...",
                stderr="",
                returncode=0
            )
        
        mock_run.side_effect = mock_git_clone
        
        repos = [
            {
                "github": "https://github.com/example/repo",
                "dest_path": "deps/example"
            }
        ]
        
        workspace_path = manager.create_workspace(
            "repo-workspace",
            repos=repos
        )
        
        # Verify git clone was called
        assert mock_run.called
        
        # Verify the workspace exists
        assert workspace_path.exists()
        
    def test_create_persistent_workspace(self, manager):
        """Test creating a persistent workspace."""
        workspace_path = manager.create_workspace(
            "persistent-ws",
            persistent=True
        )
        
        assert workspace_path.name == "persistent_persistent-ws"
        
        # Check metadata
        metadata = json.loads(
            (workspace_path / ".workspace_metadata.json").read_text()
        )
        assert metadata["persistent"] is True
        
    def test_workspace_already_exists(self, manager):
        """Test error when workspace ID already exists."""
        manager.create_workspace("duplicate")
        
        with pytest.raises(ValueError, match="already exists"):
            manager.create_workspace("duplicate")
            
    def test_get_workspace(self, manager):
        """Test retrieving workspace path."""
        workspace_path = manager.create_workspace("get-test")
        
        retrieved = manager.get_workspace("get-test")
        assert retrieved == workspace_path
        
        # Non-existent workspace
        assert manager.get_workspace("nonexistent") is None
        
    def test_cleanup_workspace(self, manager):
        """Test cleaning up a workspace."""
        workspace_path = manager.create_workspace("cleanup-test")
        
        # Verify it exists
        assert workspace_path.exists()
        assert "cleanup-test" in manager.active_workspaces
        
        # Clean it up
        result = manager.cleanup_workspace("cleanup-test")
        assert result is True
        
        # Verify it's gone
        assert not workspace_path.exists()
        assert "cleanup-test" not in manager.active_workspaces
        
    def test_cleanup_persistent_workspace(self, manager):
        """Test that persistent workspaces are not cleaned up by default."""
        workspace_path = manager.create_workspace(
            "persistent-cleanup",
            persistent=True
        )
        
        # Try to clean up without force
        result = manager.cleanup_workspace("persistent-cleanup")
        assert result is False
        assert workspace_path.exists()
        
        # Clean up with force
        result = manager.cleanup_workspace("persistent-cleanup", force=True)
        assert result is True
        assert not workspace_path.exists()
        
    def test_cleanup_all(self, manager):
        """Test cleaning up all workspaces."""
        # Create multiple workspaces
        manager.create_workspace("ws1")
        manager.create_workspace("ws2")
        manager.create_workspace("ws3", persistent=True)
        
        # Clean all non-persistent
        cleaned = manager.cleanup_all()
        assert cleaned == 2
        
        # Only persistent should remain
        assert len(manager.active_workspaces) == 1
        assert "ws3" in manager.active_workspaces
        
        # Clean all including persistent
        cleaned = manager.cleanup_all(force=True)
        assert cleaned == 1
        assert len(manager.active_workspaces) == 0
        
    def test_list_workspaces(self, manager, sample_files):
        """Test listing active workspaces."""
        # Create workspaces
        manager.create_workspace("ws1")
        manager.create_workspace("ws2", files=sample_files, persistent=True)
        
        workspaces = manager.list_workspaces()
        
        assert len(workspaces) == 2
        assert "ws1" in workspaces
        assert "ws2" in workspaces
        
        # Check workspace info
        ws1_info = workspaces["ws1"]
        assert ws1_info["exists"] is True
        assert ws1_info["persistent"] is False
        
        ws2_info = workspaces["ws2"]
        assert ws2_info["persistent"] is True
        assert len(ws2_info["resources"]["files"]) == 2
        
    def test_export_workspace(self, manager, sample_files):
        """Test exporting a workspace as archive."""
        # Create workspace with content
        workspace_path = manager.create_workspace(
            "export-test",
            files=sample_files
        )
        
        # Export it
        export_path = manager.base_dir / "exports" / "test-export.tar"
        export_path.parent.mkdir(parents=True, exist_ok=True)
        
        archive_path = manager.export_workspace("export-test", export_path)
        
        assert archive_path.exists()
        assert archive_path.suffix == ".tar"
        
    def test_export_nonexistent_workspace(self, manager):
        """Test error when exporting non-existent workspace."""
        with pytest.raises(ValueError, match="Workspace not found"):
            manager.export_workspace("nonexistent", Path("/tmp/export.tar"))
            
    def test_error_handling_during_creation(self, manager):
        """Test that workspace is cleaned up on creation error."""
        # Create invalid file mapping
        invalid_files = [
            {
                "name": "missing.txt",
                "src_path": "/nonexistent/file.txt",
                "dest_path": "."
            }
        ]
        
        with pytest.raises(FileNotFoundError):
            manager.create_workspace("error-test", files=invalid_files)
            
        # Workspace should not be in active list
        assert "error-test" not in manager.active_workspaces
        
    def test_complex_workspace(self, manager, sample_files, sample_folders):
        """Test creating a workspace with all resource types."""
        # Note: repos are mocked in other tests
        workspace_path = manager.create_workspace(
            "complex-workspace",
            files=sample_files,
            folders=sample_folders
        )
        
        # Verify all resources
        assert (workspace_path / "config" / "config.json").exists()
        assert (workspace_path / "src" / "script.py").exists()
        assert (workspace_path / "resources" / "data" / "file1.txt").exists()
        
        # Check metadata
        metadata = json.loads(
            (workspace_path / ".workspace_metadata.json").read_text()
        )
        assert len(metadata["resources"]["files"]) == 2
        assert len(metadata["resources"]["folders"]) == 1