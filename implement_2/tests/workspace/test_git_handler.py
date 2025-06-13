"""Tests for git handler operations."""

import pytest
from pathlib import Path
import subprocess
from unittest.mock import patch, MagicMock

from claude_multi_agent.workspace.git_handler import GitHandler
from claude_multi_agent.workspace.mappings import GitRepoMapping


class TestGitHandler:
    """Test GitHandler operations."""
    
    @pytest.fixture
    def handler(self):
        """Create a GitHandler instance."""
        return GitHandler()
        
    @pytest.fixture
    def workspace(self, tmp_path):
        """Create a test workspace directory."""
        workspace = tmp_path / "test_workspace"
        workspace.mkdir()
        return workspace
        
    def test_is_git_installed(self, handler):
        """Test git installation check."""
        # This should work in CI/CD environments
        result = handler.is_git_installed()
        assert isinstance(result, bool)
        
    @patch("subprocess.run")
    def test_is_git_installed_mock(self, mock_run, handler):
        """Test git installation check with mocking."""
        # Test when git is available
        mock_run.return_value = MagicMock(
            stdout="git version 2.34.1",
            returncode=0
        )
        assert handler.is_git_installed() is True
        
        # Test when git is not available
        mock_run.side_effect = FileNotFoundError()
        assert handler.is_git_installed() is False
        
    @patch("subprocess.run")
    def test_clone_repo_success(self, mock_run, handler, workspace):
        """Test successful repository cloning."""
        # Mock successful clone
        mock_run.return_value = MagicMock(
            stdout="Cloning into 'repo'...",
            stderr="",
            returncode=0
        )
        
        mapping = GitRepoMapping(
            github="https://github.com/user/repo",
            dest_path="projects/myrepo"
        )
        
        # Create fake cloned directory structure
        clone_path = workspace / "projects" / "myrepo"
        clone_path.mkdir(parents=True)
        (clone_path / ".git").mkdir()
        
        result = handler.clone_repo(workspace, mapping)
        
        # Verify git command
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "git"
        assert args[1] == "clone"
        assert "--depth" in args
        assert "1" in args
        assert mapping.github in args
        
    @patch("subprocess.run")
    def test_clone_repo_with_branch(self, mock_run, handler, workspace):
        """Test cloning a specific branch."""
        mock_run.return_value = MagicMock(
            stdout="Cloning...",
            stderr="",
            returncode=0
        )
        
        mapping = GitRepoMapping(
            github="https://github.com/user/repo",
            dest_path=".",
            branch="develop"
        )
        
        # Create fake cloned directory
        (workspace / ".git").mkdir()
        
        handler.clone_repo(workspace, mapping)
        
        # Verify branch argument
        args = mock_run.call_args[0][0]
        assert "--branch" in args
        assert "develop" in args
        
    @patch("subprocess.run")
    def test_clone_repo_deep(self, mock_run, handler, workspace):
        """Test deep cloning (not shallow)."""
        mock_run.return_value = MagicMock(
            stdout="Cloning...",
            stderr="",
            returncode=0
        )
        
        mapping = GitRepoMapping(
            github="https://github.com/user/repo",
            dest_path="deep",
            shallow=False
        )
        
        # Create fake cloned directory
        deep_path = workspace / "deep"
        deep_path.mkdir()
        (deep_path / ".git").mkdir()
        
        handler.clone_repo(workspace, mapping)
        
        # Verify no depth argument
        args = mock_run.call_args[0][0]
        assert "--depth" not in args
        
    @patch("subprocess.run")
    def test_clone_repo_failure(self, mock_run, handler, workspace):
        """Test handling of clone failure."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1,
            ["git", "clone"],
            stderr="fatal: repository not found"
        )
        
        mapping = GitRepoMapping(
            github="https://github.com/nonexistent/repo",
            dest_path="failed"
        )
        
        with pytest.raises(RuntimeError, match="Failed to clone"):
            handler.clone_repo(workspace, mapping)
            
    def test_clone_repo_validation(self, handler, workspace):
        """Test that invalid repo URLs are rejected."""
        mapping = GitRepoMapping(
            github="not-a-valid-url",
            dest_path="invalid"
        )
        
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            handler.clone_repo(workspace, mapping)
            
    @patch("subprocess.run")
    def test_clone_multiple_repos(self, mock_run, handler, workspace):
        """Test cloning multiple repositories."""
        mock_run.return_value = MagicMock(
            stdout="Cloning...",
            stderr="",
            returncode=0
        )
        
        mappings = [
            GitRepoMapping(
                github="https://github.com/user/repo1",
                dest_path="repo1"
            ),
            GitRepoMapping(
                github="https://github.com/user/repo2",
                dest_path="repo2"
            )
        ]
        
        # Create fake cloned directories
        for mapping in mappings:
            repo_path = workspace / mapping.dest_path
            repo_path.mkdir()
            (repo_path / ".git").mkdir()
            
        results = handler.clone_repos(workspace, mappings)
        
        assert len(results) == 2
        assert mock_run.call_count == 2
        
    @patch("subprocess.run")
    def test_init_repo(self, mock_run, handler, workspace):
        """Test initializing a git repository."""
        mock_run.return_value = MagicMock(
            stdout="Initialized empty Git repository",
            stderr="",
            returncode=0
        )
        
        handler.init_repo(workspace)
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == ["git", "init"]
        assert mock_run.call_args[1]["cwd"] == workspace
        
    @patch("subprocess.run")
    def test_init_repo_failure(self, mock_run, handler, workspace):
        """Test handling of init failure."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1,
            ["git", "init"],
            stderr="fatal: cannot create directory"
        )
        
        with pytest.raises(RuntimeError, match="Failed to initialize"):
            handler.init_repo(workspace)