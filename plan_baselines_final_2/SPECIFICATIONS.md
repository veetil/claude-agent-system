# Claude Multi-Agent System Specifications

## Project Overview
A high-quality system for spawning and orchestrating Claude agents using Claude Code CLI with proper session management and inter-agent communication.

## Core Requirements

### 1. Agent Management
- **Agent Creation**: Spawn individual Claude CLI processes as agents
- **Session Persistence**: Maintain conversation history across interactions
- **Isolation**: Each agent operates in its own working directory
- **Concurrency**: Support parallel agent execution

### 2. Input/Output Specifications

#### Agent Initialization Parameters
```typescript
interface AgentConfig {
  id: string;                    // Unique agent identifier
  system_prompt: string;         // Agent specialization prompt
  working_dir: string;           // Agent's isolated workspace
  allowed_tools?: string[];      // Tool permissions
  max_turns?: number;            // Max turns per interaction
}
```

#### Task Input
```typescript
interface TaskInput {
  prompt: string;                // User prompt/task
  text_input?: string;           // Additional text context
  folders?: FolderMapping[];     // Folders to map into agent workspace
  repos?: GitHubRepo[];          // GitHub repos to clone
  files?: FileMapping[];         // Files to map into agent workspace
}

interface FolderMapping {
  name: string;
  src_path: string;             // Host path
  dest_path: string;            // Relative path in agent
}

interface GitHubRepo {
  url: string;
  dest_path: string;
  branch?: string;
}

interface FileMapping {
  name: string;
  src_path: string;
  dest_path: string;
}
```

#### Output Format
```typescript
interface AgentResponse {
  session_id: string;           // Updated session ID
  result: string;               // Agent response
  metadata?: {
    tokens_used: number;
    duration_ms: number;
    tools_used: string[];
  };
}
```

### 3. Session Management Requirements
- Use Claude's native session system via `-r` flag
- Track session ID chains for each agent
- Launch Claude via interactive shell (`$SHELL -ic`)
- Maintain working directory consistency

### 4. Communication Patterns
- **Direct**: Orchestrator → Agent → Orchestrator
- **Pipeline**: Agent1 → Agent2 → Agent3
- **Parallel**: Multiple agents working simultaneously
- **Hierarchical**: Parent agents spawning child agents

### 5. File System Requirements
```
/project-root/
  /agents/
    /agent_[id]/               # Agent workspace
      /.claude/                # Session storage
      /workspace/              # Working files
      /imports/                # Mapped resources
  /shared/                     # Shared resources
  /logs/                       # System logs
```

### 6. Performance Requirements
- Agent startup: < 2 seconds
- Session resume: < 1 second
- Parallel agent limit: 10 concurrent
- Memory per agent: < 512MB

### 7. Error Handling
- Graceful degradation on API limits
- Automatic retry with exponential backoff
- Session recovery on crash
- Comprehensive error logging

### 8. Security Requirements
- API key protection
- Workspace isolation between agents
- Audit logging of all actions
- Resource access controls

## Scope Definition

### In Scope (Baseline)
1. Single agent creation and management
2. Session persistence and resumption
3. Basic file/folder mapping
4. Simple orchestrator for sequential tasks
5. JSON-based configuration
6. Command-line interface
7. Basic error handling and logging

### Future Scope (Post-Baseline)
1. Multi-agent orchestration patterns
2. Inter-agent message passing
3. Advanced scheduling and queueing
4. Web UI for monitoring
5. Distributed deployment
6. Advanced memory systems
7. Custom tool development

## Success Criteria
1. **Functional**: Agent can maintain conversation across 5+ interactions
2. **Performance**: < 2s agent startup, < 1s session resume
3. **Reliability**: 99% session persistence success rate
4. **Scalability**: Support 10 concurrent agents
5. **Usability**: Simple API requiring < 10 lines to create an agent

## Technical Constraints
1. Must use Claude CLI (not API) for session management
2. Requires interactive shell for proper functionality
3. Limited by Claude's rate limits (800 prompts/day)
4. Session files stored locally in ~/.claude/projects/
5. Python 3.8+ required
6. macOS/Linux only (Windows WSL2 supported)

## Dependencies
- Claude CLI (`@anthropic-ai/claude-code`)
- Python 3.8+
- asyncio for concurrency
- pytest for testing
- git for repository cloning
- rsync for file synchronization