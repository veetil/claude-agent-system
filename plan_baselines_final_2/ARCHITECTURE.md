# Claude Multi-Agent System Architecture

## System Overview

```mermaid
graph TB
    subgraph "User Interface Layer"
        CLI[CLI Interface]
        API[Python API]
    end
    
    subgraph "Orchestration Layer"
        OM[Orchestrator Manager]
        TQ[Task Queue]
        SM[Session Manager]
    end
    
    subgraph "Agent Layer"
        subgraph "Agent 1"
            A1[Claude Agent]
            S1[Session Tracker]
            W1[Workspace]
        end
        
        subgraph "Agent 2"
            A2[Claude Agent]
            S2[Session Tracker]
            W2[Workspace]
        end
        
        subgraph "Agent N"
            AN[Claude Agent]
            SN[Session Tracker]
            WN[Workspace]
        end
    end
    
    subgraph "Infrastructure Layer"
        CS[Claude CLI Sessions]
        FS[File System]
        PS[Process Manager]
        IS[Interactive Shell]
    end
    
    CLI --> OM
    API --> OM
    OM --> TQ
    OM --> SM
    TQ --> A1
    TQ --> A2
    TQ --> AN
    
    A1 --> S1
    A2 --> S2
    AN --> SN
    
    S1 --> CS
    S2 --> CS
    SN --> CS
    
    A1 --> W1
    A2 --> W2
    AN --> WN
    
    W1 --> FS
    W2 --> FS
    WN --> FS
    
    A1 --> IS --> PS
    A2 --> IS --> PS
    AN --> IS --> PS
```

## Component Architecture

### 1. User Interface Layer

```mermaid
classDiagram
    class CLIInterface {
        +create_agent(config)
        +send_task(agent_id, task)
        +list_agents()
        +get_history(agent_id)
    }
    
    class PythonAPI {
        +Agent(config)
        +Orchestrator(base_dir)
        +async ask(prompt)
        +async batch_ask(tasks)
    }
    
    CLIInterface --> Orchestrator
    PythonAPI --> Orchestrator
```

### 2. Orchestration Layer

```mermaid
classDiagram
    class Orchestrator {
        -agents: Dict[str, Agent]
        -base_dir: Path
        -task_queue: TaskQueue
        +create_agent(config): Agent
        +send_task(agent_id, task): Response
        +broadcast(task): List[Response]
        +pipeline(agents, task): Response
    }
    
    class TaskQueue {
        -queue: asyncio.Queue
        -workers: List[Worker]
        +enqueue(task)
        +process()
        +get_status()
    }
    
    class SessionManager {
        -sessions: Dict[str, SessionChain]
        +track_session(agent_id, session_id)
        +get_latest_session(agent_id)
        +get_history(agent_id)
    }
    
    Orchestrator --> TaskQueue
    Orchestrator --> SessionManager
    Orchestrator --> Agent
```

### 3. Agent Layer

```mermaid
classDiagram
    class Agent {
        -id: str
        -system_prompt: str
        -working_dir: Path
        -session_tracker: SessionTracker
        -shell_executor: ShellExecutor
        +ask(prompt): Response
        +ask_with_context(prompt, context): Response
        +reset_session()
    }
    
    class SessionTracker {
        -current_session_id: str
        -session_history: List[str]
        -interaction_count: int
        +update_session(new_id)
        +get_current_session()
        +get_chain()
    }
    
    class WorkspaceManager {
        -agent_dir: Path
        -imports_dir: Path
        +setup_workspace()
        +import_file(src, dest)
        +import_folder(src, dest)
        +clone_repo(url, dest)
        +cleanup()
    }
    
    Agent --> SessionTracker
    Agent --> WorkspaceManager
    Agent --> ShellExecutor
```

### 4. Infrastructure Layer

```mermaid
classDiagram
    class ShellExecutor {
        -shell: str
        +execute_claude(cmd, cwd): Result
        +parse_json_output(output): Dict
        +handle_errors(stderr): Error
    }
    
    class ProcessManager {
        -processes: Dict[str, Process]
        +spawn_process(cmd, cwd): Process
        +monitor_process(pid)
        +cleanup_zombie_processes()
    }
    
    class FileSystemManager {
        -base_path: Path
        +create_agent_workspace(agent_id)
        +sync_files(src, dest)
        +watch_directory(path, callback)
    }
    
    ShellExecutor --> ProcessManager
    WorkspaceManager --> FileSystemManager
```

## Data Flow Architecture

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Orchestrator
    participant Agent
    participant SessionTracker
    participant ShellExecutor
    participant ClaudeCLI
    
    User->>CLI: create_agent("researcher", "You are a researcher")
    CLI->>Orchestrator: create_agent(config)
    Orchestrator->>Agent: new Agent(config)
    Agent->>SessionTracker: initialize()
    Agent->>WorkspaceManager: setup_workspace()
    
    User->>CLI: ask("Research quantum computing")
    CLI->>Orchestrator: send_task("researcher", task)
    Orchestrator->>Agent: ask(prompt)
    Agent->>SessionTracker: get_current_session()
    Agent->>ShellExecutor: execute_claude(cmd, cwd)
    ShellExecutor->>ClaudeCLI: $SHELL -ic "claude -p ... -r session_id"
    ClaudeCLI-->>ShellExecutor: {session_id: "new_id", result: "..."}
    ShellExecutor-->>Agent: parsed_response
    Agent->>SessionTracker: update_session("new_id")
    Agent-->>Orchestrator: response
    Orchestrator-->>CLI: response
    CLI-->>User: display_result
```

## Session Management Architecture

```mermaid
graph LR
    subgraph "Session Lifecycle"
        I[Initial Prompt] --> S1[Session 1<br/>ID: abc123]
        S1 -->|"-r abc123"| S2[Session 2<br/>ID: def456]
        S2 -->|"-r def456"| S3[Session 3<br/>ID: ghi789]
        S3 -->|"-r ghi789"| S4[Session N<br/>ID: xyz...]
    end
    
    subgraph "File System"
        D1[~/.claude/projects/agent_1/abc123.jsonl]
        D2[~/.claude/projects/agent_1/def456.jsonl]
        D3[~/.claude/projects/agent_1/ghi789.jsonl]
        D4[~/.claude/projects/agent_1/xyz....jsonl]
    end
    
    S1 --> D1
    S2 --> D2
    S3 --> D3
    S4 --> D4
```

## Communication Patterns

### 1. Sequential Pattern
```mermaid
graph LR
    Task --> Agent1 --> Response1 --> Agent2 --> Response2 --> Result
```

### 2. Parallel Pattern
```mermaid
graph TD
    Task --> Fork
    Fork --> Agent1 --> Response1
    Fork --> Agent2 --> Response2
    Fork --> Agent3 --> Response3
    Response1 --> Join
    Response2 --> Join
    Response3 --> Join
    Join --> Result
```

### 3. Pipeline Pattern
```mermaid
graph LR
    subgraph "Pipeline"
        Input --> Designer --> Developer --> Tester --> Output
    end
```

### 4. Hierarchical Pattern
```mermaid
graph TD
    Manager --> Task1
    Manager --> Task2
    Manager --> Task3
    Task1 --> Worker1
    Task1 --> Worker2
    Task2 --> Worker3
    Task3 --> Worker4
    Task3 --> Worker5
```

## Error Handling Architecture

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Executing: send_task()
    Executing --> Success: response
    Executing --> Error: exception
    
    Error --> Retry: retryable_error
    Error --> Failed: fatal_error
    
    Retry --> Executing: backoff_wait
    Retry --> Failed: max_retries
    
    Success --> Idle: complete
    Failed --> Idle: log_error
    
    state Retry {
        [*] --> Wait
        Wait --> CheckRetries
        CheckRetries --> Continue: retries < max
        CheckRetries --> Abort: retries >= max
    }
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Local Development"
        LD[Developer Machine]
        LC[Claude CLI]
        LA[Agents]
        LD --> LC --> LA
    end
    
    subgraph "Production Single Node"
        PS[Server]
        PC[Claude CLI]
        PM[Process Manager]
        PA[Agent Pool]
        PS --> PC --> PM --> PA
    end
    
    subgraph "Production Distributed"
        LB[Load Balancer]
        N1[Node 1]
        N2[Node 2]
        N3[Node N]
        MQ[Message Queue]
        DB[Shared Storage]
        
        LB --> N1
        LB --> N2
        LB --> N3
        
        N1 --> MQ
        N2 --> MQ
        N3 --> MQ
        
        N1 --> DB
        N2 --> DB
        N3 --> DB
    end
```

## Security Architecture

```mermaid
graph TB
    subgraph "Security Layers"
        AL[API Layer]
        AUTH[Authentication]
        AUTHZ[Authorization]
        ISO[Process Isolation]
        ENC[Encryption]
        AUD[Audit Logging]
    end
    
    subgraph "Protected Resources"
        API[API Keys]
        WS[Workspaces]
        SESS[Sessions]
        LOGS[Logs]
    end
    
    AL --> AUTH
    AUTH --> AUTHZ
    AUTHZ --> ISO
    ISO --> ENC
    ENC --> AUD
    
    AUD --> API
    AUD --> WS
    AUD --> SESS
    AUD --> LOGS
```

## Key Design Decisions

1. **Interactive Shell Execution**: All Claude CLI calls go through `$SHELL -ic` to ensure proper environment loading
2. **Session Chain Tracking**: Each agent maintains a chain of session IDs for full history
3. **Workspace Isolation**: Each agent operates in its own directory for session persistence
4. **Async Architecture**: Built on asyncio for efficient concurrent agent management
5. **Stateless Agents**: Agents don't maintain internal state; all context is in Claude's sessions
6. **Event-Driven Communication**: Loose coupling between components via events
7. **Fail-Safe Design**: Comprehensive error handling and automatic recovery mechanisms