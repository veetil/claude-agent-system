"""Integration tests for workspace management with Claude CLI."""

import pytest
from pathlib import Path
import tempfile
import shutil

from claude_multi_agent.workspace import WorkspaceManager
from claude_multi_agent.shell import ShellExecutor


@pytest.mark.integration
class TestWorkspaceIntegration:
    """Integration tests combining workspace and shell execution."""
    
    @pytest.fixture
    def manager(self, tmp_path):
        """Create a WorkspaceManager."""
        return WorkspaceManager(base_dir=tmp_path / "workspaces")
        
    @pytest.fixture
    def executor(self):
        """Create a ShellExecutor."""
        return ShellExecutor()
        
    @pytest.fixture
    def sample_project(self, tmp_path):
        """Create a sample project structure."""
        project_dir = tmp_path / "sample_project"
        project_dir.mkdir()
        
        # Create Python module
        src_dir = project_dir / "src"
        src_dir.mkdir()
        
        (src_dir / "__init__.py").write_text("")
        (src_dir / "calculator.py").write_text('''
def add(a, b):
    """Add two numbers."""
    return a + b

def multiply(a, b):
    """Multiply two numbers."""
    return a * b
''')
        
        # Create test file
        (project_dir / "test_calculator.py").write_text('''
from src.calculator import add, multiply

def test_add():
    assert add(2, 3) == 5
    
def test_multiply():
    assert multiply(3, 4) == 12

if __name__ == "__main__":
    test_add()
    test_multiply()
    print("All tests passed!")
''')
        
        # Create README
        (project_dir / "README.md").write_text('''
# Sample Calculator Project

A simple calculator with add and multiply functions.

## Usage
```python
from src.calculator import add, multiply
print(add(2, 3))  # 5
print(multiply(3, 4))  # 12
```
''')
        
        return project_dir
        
    def test_workspace_with_claude_session(self, manager, executor, sample_project):
        """Test creating a workspace and using it with Claude."""
        # Create workspace with the sample project
        workspace_path = manager.create_workspace(
            "claude-test",
            folders=[{
                "name": "project",
                "src_path": str(sample_project),
                "dest_path": "."
            }]
        )
        
        # Verify project was copied
        assert (workspace_path / "project" / "src" / "calculator.py").exists()
        assert (workspace_path / "project" / "README.md").exists()
        
        # Use Claude to analyze the project
        response = executor.execute_claude(
            prompt="List all Python files in the project folder and briefly describe what each does.",
            working_dir=workspace_path
        )
        
        assert response["session_id"]
        result = response["result"].lower()
        
        # Claude should identify the files
        assert "calculator.py" in result or "calculator" in result
        assert "test_calculator.py" in result or "test" in result
        
        # Continue the session
        response2 = executor.execute_claude(
            prompt="What functions are defined in src/calculator.py?",
            session_id=response["session_id"],
            working_dir=workspace_path
        )
        
        result2 = response2["result"].lower()
        assert "add" in result2
        assert "multiply" in result2
        
    def test_multiple_workspaces_isolation(self, manager, executor):
        """Test that multiple workspaces are properly isolated."""
        # Create two workspaces with different content
        ws1_path = manager.create_workspace("workspace1")
        ws2_path = manager.create_workspace("workspace2")
        
        # Add different files to each
        manager.file_handler.write_file(
            ws1_path,
            "data.txt",
            "Workspace 1 data"
        )
        
        manager.file_handler.write_file(
            ws2_path,
            "data.txt",
            "Workspace 2 data"
        )
        
        # Start sessions in both workspaces
        response1 = executor.execute_claude(
            prompt="Read the file data.txt and tell me what it says.",
            working_dir=ws1_path
        )
        
        response2 = executor.execute_claude(
            prompt="Read the file data.txt and tell me what it says.",
            working_dir=ws2_path
        )
        
        # Verify isolation
        assert "workspace 1" in response1["result"].lower()
        assert "workspace 2" in response2["result"].lower()
        
        # Sessions should be different
        assert response1["session_id"] != response2["session_id"]
        
    @pytest.mark.skipif(not shutil.which("git"), reason="Git not available")
    def test_workspace_with_git_repo(self, manager, executor):
        """Test workspace with a cloned git repository."""
        # Use a small public repo for testing
        workspace_path = manager.create_workspace(
            "git-workspace",
            repos=[{
                "github": "https://github.com/octocat/Hello-World",
                "dest_path": "hello-world"
            }]
        )
        
        # Verify repo was cloned
        assert (workspace_path / "hello-world" / ".git").exists()
        assert (workspace_path / "hello-world" / "README").exists()
        
        # Use Claude to examine the repo
        response = executor.execute_claude(
            prompt="What files are in the hello-world directory?",
            working_dir=workspace_path
        )
        
        result = response["result"].lower()
        assert "readme" in result
        
    def test_workspace_cleanup_after_session(self, manager, executor):
        """Test cleaning up workspace after Claude session."""
        # Create workspace
        workspace_path = manager.create_workspace("temp-workspace")
        
        # Create a file
        test_file = workspace_path / "test.txt"
        test_file.write_text("Temporary data")
        
        # Use with Claude - now with --dangerously-skip-permissions
        response = executor.execute_claude(
            prompt="Create a file called output.txt with the text 'Hello from Claude'",
            working_dir=workspace_path,
            timeout=30  # Shorter timeout for test
        )
        
        # Verify file was created
        output_file = workspace_path / "output.txt"
        if not output_file.exists():
            # Log the response for debugging
            print(f"Claude response: {response.get('result', 'No result')}")
        
        assert output_file.exists(), "Claude should have created output.txt"
        assert output_file.read_text().strip() == "Hello from Claude"
        
        # Clean up workspace
        manager.cleanup_workspace("temp-workspace")
        
        # Verify cleanup
        assert not workspace_path.exists()
        assert "temp-workspace" not in manager.active_workspaces
        
    def test_persistent_workspace_survives_cleanup(self, manager, executor):
        """Test that persistent workspaces are not auto-cleaned."""
        # Create persistent workspace
        workspace_path = manager.create_workspace(
            "persistent-test",
            persistent=True
        )
        
        # Use with Claude
        response = executor.execute_claude(
            prompt="Remember this workspace is for long-term storage.",
            working_dir=workspace_path
        )
        
        session_id = response["session_id"]
        
        # Try to clean up (should fail)
        result = manager.cleanup_workspace("persistent-test")
        assert result is False
        assert workspace_path.exists()
        
        # Session should still be resumable
        response2 = executor.execute_claude(
            prompt="What did I tell you about this workspace?",
            session_id=session_id,
            working_dir=workspace_path
        )
        
        assert "long-term" in response2["result"].lower() or "storage" in response2["result"].lower()