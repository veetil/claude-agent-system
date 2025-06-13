"""Tests for workspace path mappings."""

import pytest
from pathlib import Path
import tempfile

from claude_multi_agent.workspace.mappings import (
    FileMapping, FolderMapping, GitRepoMapping, PathMapper
)


class TestFileMapping:
    """Test FileMapping validation and behavior."""
    
    def test_valid_file_mapping(self, tmp_path):
        """Test creating a valid file mapping."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        mapping = FileMapping(
            name="test.txt",
            src_path=str(test_file),
            dest_path="files"
        )
        
        # Should not raise
        mapping.validate()
        
    def test_empty_name(self, tmp_path):
        """Test that empty name is rejected."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        mapping = FileMapping(
            name="",
            src_path=str(test_file),
            dest_path="files"
        )
        
        with pytest.raises(ValueError, match="name cannot be empty"):
            mapping.validate()
            
    def test_nonexistent_source(self):
        """Test that nonexistent source file is rejected."""
        mapping = FileMapping(
            name="test.txt",
            src_path="/nonexistent/file.txt",
            dest_path="files"
        )
        
        with pytest.raises(FileNotFoundError):
            mapping.validate()
            
    def test_source_is_directory(self, tmp_path):
        """Test that directory as source is rejected."""
        mapping = FileMapping(
            name="test",
            src_path=str(tmp_path),
            dest_path="files"
        )
        
        with pytest.raises(ValueError, match="not a file"):
            mapping.validate()
            
    def test_invalid_dest_paths(self, tmp_path):
        """Test that path traversal attempts are rejected."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        # Test absolute path
        mapping = FileMapping(
            name="test.txt",
            src_path=str(test_file),
            dest_path="/etc/passwd"
        )
        
        with pytest.raises(ValueError, match="Invalid destination"):
            mapping.validate()
            
        # Test parent directory traversal
        mapping = FileMapping(
            name="test.txt",
            src_path=str(test_file),
            dest_path="../../../etc"
        )
        
        with pytest.raises(ValueError, match="Invalid destination"):
            mapping.validate()


class TestFolderMapping:
    """Test FolderMapping validation and behavior."""
    
    def test_valid_folder_mapping(self, tmp_path):
        """Test creating a valid folder mapping."""
        mapping = FolderMapping(
            name="testdir",
            src_path=str(tmp_path),
            dest_path="folders"
        )
        
        # Should not raise
        mapping.validate()
        
    def test_source_is_file(self, tmp_path):
        """Test that file as source is rejected."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        mapping = FolderMapping(
            name="test",
            src_path=str(test_file),
            dest_path="folders"
        )
        
        with pytest.raises(ValueError, match="not a folder"):
            mapping.validate()


class TestGitRepoMapping:
    """Test GitRepoMapping validation and behavior."""
    
    def test_valid_github_url(self):
        """Test valid GitHub URLs."""
        valid_urls = [
            "https://github.com/user/repo",
            "https://github.com/user/repo.git",
            "https://github.com/org-name/repo-name",
            "http://github.com/user/repo"
        ]
        
        for url in valid_urls:
            mapping = GitRepoMapping(
                github=url,
                dest_path="repos/myrepo"
            )
            # Should not raise
            mapping.validate()
            
    def test_invalid_github_urls(self):
        """Test invalid GitHub URLs are rejected."""
        invalid_urls = [
            "",
            "not-a-url",
            "https://gitlab.com/user/repo",
            "git@github.com:user/repo.git",
            "https://github.com/",
            "https://github.com/user"
        ]
        
        for url in invalid_urls:
            mapping = GitRepoMapping(
                github=url,
                dest_path="repos/myrepo"
            )
            
            with pytest.raises(ValueError):
                mapping.validate()
                
    def test_optional_fields(self):
        """Test optional branch and shallow fields."""
        mapping = GitRepoMapping(
            github="https://github.com/user/repo",
            dest_path=".",
            branch="develop",
            shallow=False
        )
        
        assert mapping.branch == "develop"
        assert mapping.shallow is False
        
        # Should validate successfully
        mapping.validate()


class TestPathMapper:
    """Test PathMapper utilities."""
    
    def test_resolve_dest_path(self, tmp_path):
        """Test safe path resolution."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        
        mapper = PathMapper()
        
        # Test normal paths
        resolved = mapper.resolve_dest_path(workspace, "files/data")
        assert resolved == workspace / "files" / "data"
        
        # Test current directory
        resolved = mapper.resolve_dest_path(workspace, ".")
        assert resolved == workspace
        
    def test_resolve_dest_path_security(self, tmp_path):
        """Test that path traversal is prevented."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        
        mapper = PathMapper()
        
        # Test absolute path
        with pytest.raises(ValueError, match="Invalid destination"):
            mapper.resolve_dest_path(workspace, "/etc/passwd")
            
        # Test parent traversal
        with pytest.raises(ValueError, match="Invalid destination"):
            mapper.resolve_dest_path(workspace, "../../../etc")
            
        # Test sneaky traversal
        with pytest.raises(ValueError, match="Invalid destination"):
            mapper.resolve_dest_path(workspace, "files/../../..")
            
    def test_create_mappings_from_dict(self, tmp_path):
        """Test creating mappings from dictionaries."""
        mapper = PathMapper()
        
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        # Test file mapping
        file_dict = {
            "name": "test.txt",
            "src_path": str(test_file),
            "dest_path": "files"
        }
        file_mapping = mapper.create_file_mapping(file_dict)
        assert file_mapping.name == "test.txt"
        assert file_mapping.src_path == str(test_file)
        assert file_mapping.dest_path == "files"
        
        # Test folder mapping
        folder_dict = {
            "name": "mydir",
            "src_path": str(tmp_path),
            "dest_path": "folders"
        }
        folder_mapping = mapper.create_folder_mapping(folder_dict)
        assert folder_mapping.name == "mydir"
        
        # Test git mapping
        git_dict = {
            "github": "https://github.com/user/repo",
            "dest_path": "repos/myrepo",
            "branch": "main"
        }
        git_mapping = mapper.create_git_mapping(git_dict)
        assert git_mapping.github == "https://github.com/user/repo"
        assert git_mapping.branch == "main"
        assert git_mapping.shallow is True  # Default value