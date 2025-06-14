"""
MCP (Model Context Protocol) support for Claude Multi-Agent System.
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List

from .utils.logging import get_logger

logger = get_logger(__name__)


class MCPManager:
    """Manages MCP configuration and environment for agents."""
    
    def __init__(self, mcp_config_path: Optional[Path] = None, env_file: Optional[Path] = None):
        """Initialize MCP manager.
        
        Args:
            mcp_config_path: Path to mcp.json file (defaults to .roo/mcp.json)
            env_file: Path to environment file (defaults to .env.mcp)
        """
        self.mcp_config_path = mcp_config_path or Path.home() / "Projects/claude-sdk/.roo/mcp.json"
        self.env_file = env_file or Path.home() / "Projects/claude-sdk/.env.mcp"
        
    def load_mcp_config(self) -> Dict[str, Any]:
        """Load MCP configuration from file."""
        if not self.mcp_config_path.exists():
            logger.warning(f"MCP config not found: {self.mcp_config_path}")
            return {}
            
        try:
            with open(self.mcp_config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load MCP config: {e}")
            return {}
    
    def load_env_vars(self) -> Dict[str, str]:
        """Load environment variables from .env.mcp file."""
        env_vars = {}
        
        if not self.env_file.exists():
            logger.warning(f"Environment file not found: {self.env_file}")
            return env_vars
            
        try:
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes if present
                        value = value.strip().strip('"').strip("'")
                        env_vars[key] = value
                        
            logger.info(f"Loaded {len(env_vars)} environment variables from {self.env_file}")
            return env_vars
            
        except Exception as e:
            logger.error(f"Failed to load environment variables: {e}")
            return {}
    
    def setup_workspace_mcp(self, workspace_path: Path) -> bool:
        """Set up MCP configuration in agent workspace.
        
        Args:
            workspace_path: Path to agent workspace
            
        Returns:
            True if setup successful, False otherwise
        """
        try:
            # Create .roo directory in workspace
            roo_dir = workspace_path / ".roo"
            roo_dir.mkdir(exist_ok=True)
            
            # Copy MCP configuration
            if self.mcp_config_path.exists():
                mcp_dst = roo_dir / "mcp.json"
                shutil.copy2(self.mcp_config_path, mcp_dst)
                logger.info(f"Copied MCP config to {mcp_dst}")
            
            # Create export-env.sh script that loads .env.mcp
            export_script = workspace_path / "export-env.sh"
            export_script.write_text("""#!/bin/bash
# Auto-generated script to load MCP environment variables

# Load .env.mcp file and export variables
if [ -f ".env.mcp" ]; then
    while IFS= read -r line || [ -n "$line" ]; do
        # Skip comments and empty lines
        if [[ $line =~ ^[[:space:]]*$ || $line =~ ^[[:space:]]*# ]]; then
            continue
        fi
        
        # Remove leading/trailing whitespace
        line=$(echo "$line" | xargs)
        
        # Export the variable
        export "$line"
    done < .env.mcp
    echo "Loaded environment variables from .env.mcp"
else
    echo "Warning: .env.mcp not found"
fi
""")
            export_script.chmod(0o755)
            
            # Copy .env.mcp if it exists
            if self.env_file.exists():
                env_dst = workspace_path / ".env.mcp"
                shutil.copy2(self.env_file, env_dst)
                logger.info(f"Copied environment file to {env_dst}")
                
                # Also create a .env symlink for compatibility
                env_link = workspace_path / ".env"
                if not env_link.exists():
                    env_link.symlink_to(".env.mcp")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup MCP in workspace: {e}")
            return False
    
    def get_mcp_env(self) -> Dict[str, str]:
        """Get environment variables for MCP execution."""
        # Start with current environment
        env = os.environ.copy()
        
        # Add MCP-specific variables
        mcp_vars = self.load_env_vars()
        env.update(mcp_vars)
        
        return env
    
    def prepare_claude_command(self, base_args: List[str], enable_mcp: bool = True) -> List[str]:
        """Prepare Claude command with MCP support.
        
        Args:
            base_args: Base command arguments
            enable_mcp: Whether to enable MCP
            
        Returns:
            Modified command arguments
        """
        if not enable_mcp:
            return base_args
            
        # Check if --mcp-config is already present
        if "--mcp-config" in base_args:
            return base_args
            
        # Add MCP config if available
        if self.mcp_config_path.exists():
            # Find where to insert --mcp-config (before -p prompt)
            insert_idx = 0
            for i, arg in enumerate(base_args):
                if arg == "-p":
                    insert_idx = i
                    break
            
            # Insert --mcp-config
            new_args = base_args[:insert_idx]
            new_args.extend(["--mcp-config", str(self.mcp_config_path)])
            new_args.extend(base_args[insert_idx:])
            
            logger.debug(f"Added --mcp-config to command")
            return new_args
            
        return base_args
    
    def test_mcp_setup(self, workspace_path: Path) -> bool:
        """Test if MCP is properly set up in workspace.
        
        Args:
            workspace_path: Path to workspace
            
        Returns:
            True if MCP is properly configured
        """
        # Check for required files
        required_files = [
            workspace_path / ".roo" / "mcp.json",
            workspace_path / "export-env.sh",
            workspace_path / ".env.mcp"
        ]
        
        for file_path in required_files:
            if not file_path.exists():
                logger.warning(f"Missing MCP file: {file_path}")
                return False
                
        # Test environment loading
        try:
            result = subprocess.run(
                ["bash", "-c", "source ./export-env.sh && echo 'OK'"],
                cwd=str(workspace_path),
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0 or "OK" not in result.stdout:
                logger.warning("Failed to load MCP environment")
                return False
                
        except Exception as e:
            logger.error(f"Error testing MCP setup: {e}")
            return False
            
        logger.info("MCP setup verified successfully")
        return True