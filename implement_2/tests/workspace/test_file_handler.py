"""Tests for file handler operations."""

import pytest
from pathlib import Path
import tempfile

from claude_multi_agent.workspace.file_handler import FileHandler
from claude_multi_agent.workspace.mappings import FileMapping, FolderMapping


class TestFileHandler:
    """Test FileHandler operations."""
    
    @pytest.fixture
    def handler(self):
        """Create a FileHandler instance."""
        return FileHandler()
        
    @pytest.fixture
    def workspace(self, tmp_path):
        """Create a test workspace directory."""
        workspace = tmp_path / "test_workspace"
        workspace.mkdir()
        return workspace
        
    def test_copy_single_file(self, handler, workspace, tmp_path):
        """Test copying a single file."""
        # Create source file
        src_file = tmp_path / "source.txt"
        src_file.write_text("Hello, World!")
        
        # Create mapping
        mapping = FileMapping(
            name="copied.txt",
            src_path=str(src_file),
            dest_path="files/data"
        )
        
        # Copy file
        dest_path = handler.copy_file(workspace, mapping)
        
        # Verify
        assert dest_path.exists()
        assert dest_path == workspace / "files" / "data" / "copied.txt"
        assert dest_path.read_text() == "Hello, World!"
        
    def test_copy_file_to_root(self, handler, workspace, tmp_path):
        """Test copying a file to workspace root."""
        # Create source file
        src_file = tmp_path / "source.txt"
        src_file.write_text("Root file")
        
        # Create mapping to root
        mapping = FileMapping(
            name="root.txt",
            src_path=str(src_file),
            dest_path="."
        )
        
        # Copy file
        dest_path = handler.copy_file(workspace, mapping)
        
        # Verify
        assert dest_path == workspace / "root.txt"
        assert dest_path.read_text() == "Root file"
        
    def test_copy_nonexistent_file(self, handler, workspace):
        """Test error handling for nonexistent source file."""
        mapping = FileMapping(
            name="missing.txt",
            src_path="/nonexistent/file.txt",
            dest_path="files"
        )
        
        with pytest.raises(FileNotFoundError):
            handler.copy_file(workspace, mapping)
            
    def test_copy_folder(self, handler, workspace, tmp_path):
        """Test copying a folder with contents."""
        # Create source folder structure
        src_folder = tmp_path / "source_folder"
        src_folder.mkdir()
        (src_folder / "file1.txt").write_text("File 1")
        (src_folder / "subdir").mkdir()
        (src_folder / "subdir" / "file2.txt").write_text("File 2")
        
        # Create mapping
        mapping = FolderMapping(
            name="copied_folder",
            src_path=str(src_folder),
            dest_path="data"
        )
        
        # Copy folder
        dest_path = handler.copy_folder(workspace, mapping)
        
        # Verify structure
        assert dest_path == workspace / "data" / "copied_folder"
        assert (dest_path / "file1.txt").read_text() == "File 1"
        assert (dest_path / "subdir" / "file2.txt").read_text() == "File 2"
        
    def test_copy_folder_overwrites_existing(self, handler, workspace, tmp_path):
        """Test that copying a folder overwrites existing content."""
        # Create source folder
        src_folder = tmp_path / "source"
        src_folder.mkdir()
        (src_folder / "new.txt").write_text("New content")
        
        # Create existing folder in workspace
        existing = workspace / "existing_folder"
        existing.mkdir()
        (existing / "old.txt").write_text("Old content")
        
        # Create mapping
        mapping = FolderMapping(
            name="existing_folder",
            src_path=str(src_folder),
            dest_path="."
        )
        
        # Copy folder (should overwrite)
        dest_path = handler.copy_folder(workspace, mapping)
        
        # Verify new content
        assert dest_path == existing
        assert (dest_path / "new.txt").exists()
        assert (dest_path / "new.txt").read_text() == "New content"
        assert not (dest_path / "old.txt").exists()
        
    def test_copy_multiple_files(self, handler, workspace, tmp_path):
        """Test copying multiple files at once."""
        # Create source files
        files = []
        for i in range(3):
            src_file = tmp_path / f"file{i}.txt"
            src_file.write_text(f"Content {i}")
            
            mapping = FileMapping(
                name=f"file{i}.txt",
                src_path=str(src_file),
                dest_path="batch"
            )
            files.append(mapping)
            
        # Copy all files
        results = handler.copy_files(workspace, files)
        
        # Verify
        assert len(results) == 3
        for i, dest in enumerate(results):
            assert dest.name == f"file{i}.txt"
            assert dest.read_text() == f"Content {i}"
            
    def test_copy_files_with_error(self, handler, workspace, tmp_path):
        """Test that error in one file stops the batch."""
        # Create one valid file and one invalid
        valid_file = tmp_path / "valid.txt"
        valid_file.write_text("Valid")
        
        mappings = [
            FileMapping(
                name="valid.txt",
                src_path=str(valid_file),
                dest_path="."
            ),
            FileMapping(
                name="invalid.txt",
                src_path="/nonexistent/file.txt",
                dest_path="."
            )
        ]
        
        # Should raise on invalid file
        with pytest.raises(FileNotFoundError):
            handler.copy_files(workspace, mappings)
            
    def test_create_directory(self, handler, workspace):
        """Test creating directories."""
        # Create nested directory
        dir_path = handler.create_directory(workspace, "path/to/new/dir")
        
        assert dir_path.exists()
        assert dir_path.is_dir()
        assert dir_path == workspace / "path" / "to" / "new" / "dir"
        
    def test_write_file(self, handler, workspace):
        """Test writing content to a file."""
        # Write file
        file_path = handler.write_file(
            workspace,
            "config/settings.json",
            '{"key": "value"}'
        )
        
        # Verify
        assert file_path.exists()
        assert file_path == workspace / "config" / "settings.json"
        assert file_path.read_text() == '{"key": "value"}'
        
    def test_security_checks(self, handler, workspace, tmp_path):
        """Test that path traversal attempts are blocked."""
        src_file = tmp_path / "evil.txt"
        src_file.write_text("Evil content")
        
        # Try to escape workspace
        mapping = FileMapping(
            name="evil.txt",
            src_path=str(src_file),
            dest_path="../../../etc"
        )
        
        with pytest.raises(ValueError, match="Invalid destination"):
            handler.copy_file(workspace, mapping)