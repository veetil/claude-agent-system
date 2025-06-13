# Claude CLI Integration Updates

## Key Documentation Findings

After reviewing the Claude CLI documentation, here are the critical updates that should be incorporated into our multi-agent system plan:

### 1. SDK Print Mode is Purpose-Built for Our Use Case

The CLI provides a non-interactive print mode (`-p` flag) specifically designed for programmatic usage:
- **JSON Output Format**: `--output-format json` provides structured responses with metadata
- **Stream JSON**: `--output-format stream-json` for real-time feedback
- **Session Management**: Each response includes `session_id` for conversation continuity
- **Exit Codes**: Proper exit codes for error handling

### 2. Session-Based Architecture

Claude CLI has built-in session management that we should leverage:
- `--continue` to continue the most recent conversation
- `--resume <session-id>` to resume specific sessions
- Sessions maintain full context across interactions
- Perfect for our agent continuity requirements

### 3. System Prompt Customization

Critical for agent specialization:
- `--system-prompt` to completely override default prompts
- `--append-system-prompt` to add to existing prompts
- Only works with `-p` flag (perfect for our use case)
- Enables true agent specialization

### 4. Permission Management

Built-in permission system that we can leverage:
- `--allowedTools` and `--disallowedTools` for fine-grained control
- `--dangerously-skip-permissions` for automated environments
- Permission rules support patterns like `Bash(npm run test:*)`
- Can be configured via settings.json files

### 5. Memory System

CLAUDE.md files provide persistent memory:
- Project-level: `./CLAUDE.md`
- User-level: `~/.claude/CLAUDE.md`
- Supports imports with `@path/to/file` syntax
- Perfect for agent-specific instructions

### 6. Environment and Configuration

Hierarchical configuration system:
- User settings: `~/.claude/settings.json`
- Project settings: `.claude/settings.json`
- Local project settings: `.claude/settings.local.json`
- Enterprise policies: `/etc/claude-code/policies.json`

### 7. Authentication Options

Multiple authentication methods:
- API Key via `ANTHROPIC_API_KEY` environment variable
- OAuth through Anthropic Console
- Enterprise platforms (Bedrock, Vertex AI)
- Custom auth via `apiKeyHelper` script

## Architecture Improvements

### 1. Use SDK Mode Exclusively

Update CLIProcessManager to always use print mode:
```typescript
const args = [
  '-p',
  prompt,
  '--output-format', 'json',
  '--system-prompt', agentConfig.systemPrompt,
  '--max-turns', String(agentConfig.maxTurns || 10),
  '--dangerously-skip-permissions' // For automation
];
```

### 2. Session-Based Agent State

Each agent maintains its session ID:
```typescript
interface IAgentState {
  sessionId: string;
  lastActivity: Date;
  taskCount: number;
  context: IAgentContext;
}
```

### 3. Structured Response Handling

Parse JSON responses properly:
```typescript
interface ClaudeSDKResponse {
  type: 'result';
  subtype: 'success' | 'error_max_turns';
  cost_usd: number;
  duration_ms: number;
  duration_api_ms: number;
  is_error: boolean;
  num_turns: number;
  result?: string;
  session_id: string;
}
```

### 4. Memory-Based Agent Configuration

Use CLAUDE.md for agent instructions:
```
# Research Agent Instructions

You are a specialized research agent focused on:
- Deep analysis of technical topics
- Citing credible sources
- Structured output format

## Output Format
Always structure research as:
1. Executive Summary
2. Detailed Findings
3. Sources and Citations
```

### 5. Permission Profiles

Define permission profiles per agent type:
```json
{
  "research-agent": {
    "permissions": {
      "allow": [
        "Read(*)",
        "Bash(grep:*)",
        "Bash(find:*)"
      ],
      "deny": [
        "Edit(*)",
        "Bash(rm:*)",
        "Bash(git push:*)"
      ]
    }
  }
}
```

## Updated Implementation Priorities

### High Priority Changes

1. **Rewrite Step 0 POC**: Focus on SDK print mode validation
2. **Update CLIProcessManager**: Use JSON output exclusively
3. **Implement Session Management**: Track and reuse session IDs
4. **Create Agent Memory Templates**: CLAUDE.md per agent type
5. **Define Permission Profiles**: Settings.json configurations

### Medium Priority Changes

1. **Streaming Support**: Implement stream-json parsing
2. **Cost Tracking**: Use cost_usd from responses
3. **Turn Limiting**: Implement --max-turns per task
4. **Memory Imports**: Leverage @import syntax

### Low Priority Changes

1. **Enterprise Authentication**: Support for Bedrock/Vertex
2. **Custom Auth Scripts**: apiKeyHelper integration
3. **Policy Management**: Enterprise policy support

## Validation Updates

### Success Criteria
- ✅ SDK print mode returns valid JSON
- ✅ Sessions maintain context across calls
- ✅ System prompts customize agent behavior
- ✅ Permission system allows required operations
- ✅ Memory files load correctly
- ✅ Multiple agents can run concurrently

### Risk Mitigation
- Always use JSON output for parsing reliability
- Store session IDs for crash recovery
- Use --dangerously-skip-permissions cautiously
- Implement proper error handling for JSON parsing
- Monitor cost_usd to prevent runaway expenses

## Conclusion

The Claude CLI is well-designed for our use case with its SDK print mode. The session management, structured output, and permission system provide a solid foundation for our multi-agent system. These updates should be incorporated into the implementation plan to leverage the full capabilities of Claude CLI.