"""Integration tests for ShellExecutor with real Claude CLI"""

import pytest
import tempfile
import time
from pathlib import Path

from claude_multi_agent.shell.executor import ShellExecutor
from claude_multi_agent.core.exceptions import SessionError


@pytest.mark.integration
class TestShellExecutorIntegration:
    """End-to-end integration tests with real Claude CLI"""
    
    def test_complete_conversation_flow(self):
        """Test a complete conversation flow with session management"""
        executor = ShellExecutor()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            
            # Step 1: Start a new conversation
            print("\n=== Starting new conversation ===")
            result1 = executor.execute_claude(
                prompt="I'm going to tell you a story. The main character is named Alice. Say 'Ready to hear about Alice'",
                working_dir=workspace
            )
            
            print(f"Initial response: {result1}")
            assert "session_id" in result1
            assert "Alice" in result1["result"]
            session1 = result1["session_id"]
            
            # Step 2: Continue with context
            print("\n=== Continuing conversation ===")
            result2 = executor.execute_claude(
                prompt="Alice lives in a blue house. What color is her house?",
                session_id=session1,
                working_dir=workspace
            )
            
            print(f"Continued response: {result2}")
            assert "blue" in result2["result"].lower()
            session2 = result2["session_id"]
            
            # Step 3: Test memory retention
            print("\n=== Testing memory ===")
            result3 = executor.execute_claude(
                prompt="What was the name of the main character I mentioned?",
                session_id=session2,
                working_dir=workspace
            )
            
            print(f"Memory test response: {result3}")
            assert "Alice" in result3["result"]
            
            # Step 4: Final context check
            print("\n=== Final context check ===")
            result4 = executor.execute_claude(
                prompt="Tell me everything you remember about the character",
                session_id=result3["session_id"],
                working_dir=workspace
            )
            
            print(f"Final response: {result4}")
            response_text = result4["result"].lower()
            assert "alice" in response_text
            assert "blue" in response_text or "house" in response_text
    
    def test_parallel_isolated_sessions(self):
        """Test that parallel sessions in different directories are isolated"""
        executor = ShellExecutor()
        
        with tempfile.TemporaryDirectory() as tmpdir1:
            with tempfile.TemporaryDirectory() as tmpdir2:
                workspace1 = Path(tmpdir1)
                workspace2 = Path(tmpdir2)
                
                print(f"\n=== Testing parallel sessions ===")
                print(f"Workspace 1: {workspace1}")
                print(f"Workspace 2: {workspace2}")
                
                # Create two different contexts
                result1 = executor.execute_claude(
                    prompt="My favorite color is RED. Remember this.",
                    working_dir=workspace1
                )
                
                result2 = executor.execute_claude(
                    prompt="My favorite color is GREEN. Remember this.",
                    working_dir=workspace2
                )
                
                # Verify isolation
                check1 = executor.execute_claude(
                    prompt="What is my favorite color?",
                    session_id=result1["session_id"],
                    working_dir=workspace1
                )
                
                check2 = executor.execute_claude(
                    prompt="What is my favorite color?",
                    session_id=result2["session_id"],
                    working_dir=workspace2
                )
                
                print(f"Workspace 1 remembers: {check1['result']}")
                print(f"Workspace 2 remembers: {check2['result']}")
                
                # Each should remember its own color
                assert "red" in check1["result"].lower()
                assert "green" in check2["result"].lower()
                
                # And not the other's color
                assert "green" not in check1["result"].lower()
                assert "red" not in check2["result"].lower()
    
    def test_error_recovery(self):
        """Test error recovery and retry logic"""
        executor = ShellExecutor()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            
            # Start a conversation
            result = executor.execute_claude(
                prompt="Hello, this is a test",
                working_dir=workspace
            )
            
            valid_session = result["session_id"]
            
            # Try invalid session (should fail but not crash)
            with pytest.raises(SessionError):
                executor.execute_claude(
                    prompt="Continue",
                    session_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",  # Valid UUID format but doesn't exist
                    working_dir=workspace
                )
            
            # Valid session should still work after error
            result2 = executor.execute_claude(
                prompt="Are you still there?",
                session_id=valid_session,
                working_dir=workspace
            )
            
            assert "session_id" in result2
            assert result2["session_id"] is not None
    
    def test_complex_multiline_interaction(self):
        """Test handling of complex multiline prompts and responses"""
        executor = ShellExecutor()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            
            # Send a complex multiline prompt
            complex_prompt = """Please help me with the following tasks:
1. Create a shopping list with 5 items
2. Each item should have a quantity
3. Format it nicely

Please be concise."""
            
            result = executor.execute_claude(
                prompt=complex_prompt,
                working_dir=workspace
            )
            
            print(f"\n=== Complex response ===\n{result['result']}")
            
            # Should handle multiline response properly
            response = result["result"]
            assert len(response.split('\n')) > 3  # Should be multiple lines
            assert any(char.isdigit() for char in response)  # Should contain numbers
    
    @pytest.mark.asyncio
    async def test_async_execution(self):
        """Test async execution capabilities"""
        executor = ShellExecutor()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            
            # Test async execution
            result = await executor.execute_claude_async(
                prompt="Say 'Async test successful'",
                working_dir=workspace
            )
            
            assert "Async test successful" in result["result"]
            
            # Test async session continuation
            result2 = await executor.execute_claude_async(
                prompt="What did you just say?",
                session_id=result["session_id"],
                working_dir=workspace
            )
            
            assert "async" in result2["result"].lower()
    
    def test_performance_and_timing(self):
        """Test performance characteristics and timeouts"""
        executor = ShellExecutor()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            
            # Measure response time
            start_time = time.time()
            result = executor.execute_claude(
                prompt="Say 'Quick response'",
                working_dir=workspace
            )
            elapsed = time.time() - start_time
            
            print(f"\n=== Performance test ===")
            print(f"Response time: {elapsed:.2f} seconds")
            print(f"Response: {result}")
            
            # Should complete in reasonable time
            assert elapsed < 30  # 30 seconds max
            assert "Quick response" in result["result"]