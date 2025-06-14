# MCP (Model Context Protocol) Integration

This document describes how to use MCP servers with the Claude Multi-Agent System.

## Overview

Model Context Protocol (MCP) is an open standard created by Anthropic that provides a universal way for AI models to interact with external data sources and tools. Our multi-agent system fully supports MCP, allowing agents to:

- Access GitHub repositories and APIs
- Search the web using Perplexity
- Control browsers with Puppeteer
- Query databases with Supabase
- Scrape and analyze web content with Firecrawl
- And more...

## Setup

### 1. MCP Configuration

Place your MCP server configuration in `.roo/mcp.json`:

```json
{
  "mcpServers": {
    "github": {
      "command": "node",
      "args": [
        "/path/to/mcp-server-github/dist/index.js"
      ],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    // ... other servers
  }
}
```

### 2. Environment Variables

Create a `.env.mcp` file with your API keys:

```bash
# GitHub
GITHUB_TOKEN='your_github_token_here'

# Perplexity
PERPLEXITY_API_KEY='your_perplexity_key_here'

# Other services...
```

### 3. Update export-env.sh

The `export-env.sh` script now loads from `.env.mcp` instead of `.env`.

## Usage

### Basic Usage

Enable MCP when running an agent:

```python
from claude_multi_agent import run_agent_with_io

result = run_agent_with_io(
    prompt="Use GitHub MCP to search for 'claude' repositories",
    enable_mcp=True  # Enable MCP support
)
```

### Advanced Usage with Custom Paths

```python
result = run_agent_with_io(
    prompt="Your prompt here",
    enable_mcp=True,
    mcp_config_path=Path("/custom/path/to/mcp.json"),
    mcp_env_file=Path("/custom/path/to/.env.mcp")
)
```

### Using with Task JSON Files

In your task JSON file:

```json
{
    "prompt": "Use MCP servers to accomplish the task",
    "enable_mcp": true,
    "mcp_config_path": null,  // Uses default
    "mcp_env_file": null,      // Uses default
    // ... other config
}
```

### Command Line Usage

```bash
# Enable MCP from command line
python run_agent_advanced.py --task task.json --enable-mcp

# With custom paths
python run_agent_advanced.py --task task.json \
    --enable-mcp \
    --mcp-config /path/to/mcp.json \
    --mcp-env /path/to/.env.mcp
```

## Real-time Debug Output

To see MCP operations as they happen:

```python
result = run_agent_with_io(
    prompt="Your prompt",
    enable_mcp=True,
    realtime_debug=True  # Shows streaming output
)
```

Or from command line:

```bash
python run_agent_advanced.py --task task.json --enable-mcp --realtime-debug
```

## Available MCP Servers

Based on your `.roo/mcp.json`, you have access to:

1. **GitHub** - Repository operations, issues, PRs, etc.
2. **Perplexity** - Web search and question answering
3. **Puppeteer** - Browser automation
4. **Firecrawl** - Web scraping and content extraction
5. **Supabase** - Database operations

## Example Tasks

### 1. GitHub Repository Search

```python
prompt = """
Use the GitHub MCP server to search for repositories 
related to 'machine learning'. Show the top 5 results with:
- Repository name and owner
- Description
- Star count
- Primary language
"""
```

### 2. Web Research

```python
prompt = """
Use the Perplexity MCP server to research:
'What are the latest advances in AI agents in 2025?'
Provide a summary with key points.
"""
```

### 3. Multi-Server Task

```python
prompt = """
1. Use GitHub MCP to find info about 'anthropics/anthropic-sdk-python'
2. Use Perplexity MCP to search for tutorials about this SDK
3. Create a combined report with findings from both sources
"""
```

## How It Works

When MCP is enabled:

1. The MCPManager loads your MCP configuration and environment variables
2. MCP files are copied to the agent's workspace:
   - `.roo/mcp.json` - Server configurations
   - `.env.mcp` - Environment variables
   - `export-env.sh` - Script to load env vars
3. The shell executor adds `--mcp-config` flag to Claude CLI
4. Environment variables are passed to the subprocess
5. Claude can now use MCP tools via `mcp__<server>__<function>` commands

## Troubleshooting

### MCP servers not available

Check that:
1. `.roo/mcp.json` exists and is valid JSON
2. Server paths in `mcp.json` are correct
3. Required npm packages are installed

### Authentication errors

Verify that:
1. `.env.mcp` contains valid API keys
2. Environment variables are being loaded (check with `source export-env.sh`)
3. API keys have necessary permissions

### Real-time debug

Use `--realtime-debug` to see:
- Which MCP servers are connected
- Tool calls being made
- Responses from MCP servers
- Any errors that occur

## Security Notes

- Keep `.env.mcp` secure and never commit it to version control
- Use minimal permissions for API tokens
- The `--dangerously-skip-permissions` flag is always used for autonomous operation
- MCP servers run in isolated processes

## Examples

See the `examples/tasks/` directory for complete examples:
- `mcp_github_task.json` - GitHub repository search
- `mcp_multi_server_task.json` - Using multiple MCP servers

Run the test script to verify your setup:
```bash
python test_mcp_integration.py
```

Or try the demo:
```bash
python test_mcp_demo.py
```