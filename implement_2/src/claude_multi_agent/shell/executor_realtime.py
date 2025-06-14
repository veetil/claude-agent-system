"""
Real-time output version of ShellExecutor using threading.
This approach reads stdout/stderr in separate threads for real-time logging.
"""

import os
import json
import shlex
import subprocess
import threading
import queue
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

from ..utils.retry import retry_with_backoff
from ..utils.logging import get_logger
from ..core.exceptions import ExecutionError, SessionError

logger = get_logger(__name__)


class RealtimeShellExecutor:
    """Execute Claude CLI commands with real-time output streaming"""
    
    def __init__(self, shell: Optional[str] = None):
        """Initialize the executor
        
        Args:
            shell: Shell to use (defaults to $SHELL or /bin/bash)
        """
        self.shell = shell or os.environ.get("SHELL", "/bin/bash")
        logger.info(f"Initialized RealtimeShellExecutor with shell: {self.shell}")
        self._validate_shell()
    
    def _validate_shell(self):
        """Ensure shell is available and executable"""
        if not Path(self.shell).exists():
            raise ExecutionError(f"Shell not found: {self.shell}")
    
    def _build_claude_command(
        self, 
        prompt: str, 
        session_id: Optional[str] = None,
        output_format: str = "json",
        debug: bool = False
    ) -> List[str]:
        """Build Claude CLI command arguments"""
        args = [
            "claude", 
            "--dangerously-skip-permissions",
            "-p", prompt, 
            "--output-format", output_format
        ]
        
        if debug:
            args.append("--debug")
            
        if session_id:
            args.extend(["-r", session_id])
            
        return args
    
    def _read_stream(self, stream, stream_name: str, output_queue: queue.Queue, debug: bool):
        """Read from a stream and log/queue output in real-time"""
        try:
            for line in iter(stream.readline, ''):
                if line:
                    line = line.rstrip()
                    output_queue.put(line)
                    if debug and line.strip():
                        # Log with timestamp for better debugging
                        timestamp = time.strftime("%H:%M:%S")
                        logger.info(f"[{timestamp}] [{stream_name}] {line}")
        except Exception as e:
            logger.error(f"Error reading {stream_name}: {e}")
        finally:
            stream.close()
    
    def _sanitize_output(self, output: str) -> str:
        """Remove shell artifacts and find JSON content"""
        lines = output.strip().split('\n')
        
        # Find first line that starts with '{'
        json_start_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith('{'):
                json_start_idx = i
                break
                
        if json_start_idx is None:
            raise ExecutionError("No JSON found in output")
            
        # Extract JSON lines using brace counting
        json_lines = []
        brace_count = 0
        
        for line in lines[json_start_idx:]:
            json_lines.append(line)
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0:
                break
                
        return '\n'.join(json_lines)
    
    def _handle_error(self, stderr: str, session_id: Optional[str]):
        """Parse and handle specific errors from Claude CLI"""
        error_lower = stderr.lower()
        
        if "no conversation found with session id" in error_lower:
            raise SessionError(f"Session not found: {session_id}")
        elif "not a valid uuid" in error_lower:
            raise SessionError(f"Invalid session ID format: {session_id}")
        elif "rate limit" in error_lower:
            raise ExecutionError("Rate limit exceeded")
        else:
            raise ExecutionError(f"Claude CLI error: {stderr}")
    
    @retry_with_backoff(max_attempts=3, exceptions=(ExecutionError,))
    def execute_claude(
        self, 
        prompt: str, 
        session_id: Optional[str] = None,
        working_dir: Optional[Path] = None,
        timeout: int = 300,
        debug: bool = False
    ) -> Dict[str, Any]:
        """Execute Claude CLI command with real-time output
        
        Args:
            prompt: The prompt to send to Claude
            session_id: Optional session ID to resume
            working_dir: Working directory for command execution
            timeout: Command timeout in seconds
            debug: Enable Claude CLI debug mode and real-time output
            
        Returns:
            Parsed JSON response with session_id and result
        """
        # Build command
        args = self._build_claude_command(prompt, session_id, debug=debug)
        shell_cmd = " ".join(shlex.quote(arg) for arg in args)
        
        # Set working directory
        cwd = str(working_dir) if working_dir else os.getcwd()
        
        logger.debug(f"Executing: {shell_cmd} in {cwd}")
        
        if debug:
            logger.info("=== Claude CLI Real-time Debug Output ===")
            logger.info(f"Command: {shell_cmd}")
            logger.info(f"Working dir: {cwd}")
        
        try:
            # Execute via interactive shell
            proc = subprocess.Popen(
                [self.shell, "-ic", shell_cmd],
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )
            
            # Create queues for output
            stdout_queue = queue.Queue()
            stderr_queue = queue.Queue()
            
            # Start threads to read output
            stdout_thread = threading.Thread(
                target=self._read_stream,
                args=(proc.stdout, "STDOUT", stdout_queue, debug),
                daemon=True
            )
            stderr_thread = threading.Thread(
                target=self._read_stream,
                args=(proc.stderr, "STDERR", stderr_queue, debug),
                daemon=True
            )
            
            stdout_thread.start()
            stderr_thread.start()
            
            # Wait for process with timeout
            try:
                proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                raise ExecutionError(f"Command timed out after {timeout}s")
            
            # Give threads a moment to finish reading
            stdout_thread.join(timeout=1)
            stderr_thread.join(timeout=1)
            
            # Collect all output
            stdout_lines = []
            stderr_lines = []
            
            while not stdout_queue.empty():
                stdout_lines.append(stdout_queue.get_nowait())
            
            while not stderr_queue.empty():
                stderr_lines.append(stderr_queue.get_nowait())
            
            if debug:
                logger.info("=== End Real-time Debug Output ===")
                logger.info(f"Process exited with code: {proc.returncode}")
            
            # Join output
            full_stdout = '\n'.join(stdout_lines)
            full_stderr = '\n'.join(stderr_lines)
            
            if proc.returncode != 0:
                self._handle_error(full_stderr, session_id)
                
            # Parse response
            clean_output = self._sanitize_output(full_stdout)
            response = json.loads(clean_output)
            
            logger.debug(f"Response: {response}")
            return response
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            if 'full_stdout' in locals():
                logger.error(f"Raw output: {full_stdout}")
            raise ExecutionError(f"Failed to parse Claude response: {e}")
        except SessionError:
            raise
        except ExecutionError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise ExecutionError(f"Command execution failed: {e}")
    
    async def execute_claude_async(
        self, 
        prompt: str, 
        session_id: Optional[str] = None,
        working_dir: Optional[Path] = None,
        timeout: int = 300,
        debug: bool = False
    ) -> Dict[str, Any]:
        """Async version of execute_claude"""
        import asyncio
        return await asyncio.to_thread(
            self.execute_claude,
            prompt,
            session_id,
            working_dir,
            timeout,
            debug
        )