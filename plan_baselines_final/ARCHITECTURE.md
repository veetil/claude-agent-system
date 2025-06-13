# Claude Multi-Agent System Architecture

## Executive Summary

The Claude Multi-Agent System is designed to spawn and orchestrate multiple Claude CLI agents working collaboratively on software engineering tasks. The architecture emphasizes isolation, scalability, and conflict prevention while maintaining high performance and reliability.

## System Architecture Overview

```mermaid
graph TB
    subgraph "User Interface Layer"
        CLI[CLI Interface]
        API[REST API]
        WS[WebSocket API]
    end

    subgraph "Orchestration Layer"
        O[Orchestrator]
        TD[Task Distributor]
        CM[Conflict Manager]
        RM[Resource Monitor]
    end

    subgraph "Agent Layer"
        A1[Research Agent]
        A2[Code Agent]
        A3[Review Agent]
        A4[Test Agent]
        AN[... More Agents]
    end

    subgraph "Communication Layer"
        MQ[Message Queue]
        ES[Event Stream]
        DLQ[Dead Letter Queue]
    end

    subgraph "Process Management Layer"
        CPM[CLI Process Manager]
        TP[Terminal Pool]
        SM[Session Manager]
        CB[Circuit Breaker]
    end

    subgraph "Repository Management Layer"
        WM[Worktree Manager]
        FL[File Lock Manager]
        CD[Conflict Detector]
        VS[Version Control]
    end

    subgraph "Storage Layer"
        FS[File System]
        MS[Memory Store]
        SS[Session Store]
        LS[Lock Store]
    end

    CLI --> O
    API --> O
    WS --> O

    O --> TD
    O --> CM
    O --> RM

    TD --> MQ
    CM --> MQ
    
    MQ --> A1
    MQ --> A2
    MQ --> A3
    MQ --> A4
    MQ --> AN

    A1 --> CPM
    A2 --> CPM
    A3 --> CPM
    A4 --> CPM

    CPM --> TP
    CPM --> SM
    CPM --> CB

    A1 --> WM
    A2 --> WM
    A3 --> WM
    A4 --> WM

    WM --> FL
    WM --> CD
    WM --> VS

    TP --> FS
    SM --> SS
    FL --> LS
    MS --> FS

    MQ --> DLQ
    ES --> MQ
```

## Component Architecture

### 1. Orchestration Layer

```mermaid
classDiagram
    class Orchestrator {
        -taskQueue: TaskQueue
        -agentPool: AgentPool
        -conflictManager: ConflictManager
        +initialize(): Promise~void~
        +submitTask(task: ITask): Promise~string~
        +getTaskStatus(taskId: string): TaskStatus
        +shutdown(): Promise~void~
    }

    class TaskDistributor {
        -conflictGraph: Graph
        -scheduler: TaskScheduler
        +distributeTasks(tasks: ITask[]): TaskAssignment[]
        +optimizeDistribution(): void
        +rebalanceTasks(): void
    }

    class ConflictManager {
        -lockManager: FileLockManager
        -detector: ConflictDetector
        +checkConflicts(task: ITask): Conflict[]
        +resolveConflict(conflict: Conflict): Resolution
        +preventConflicts(tasks: ITask[]): void
    }

    Orchestrator --> TaskDistributor
    Orchestrator --> ConflictManager
    TaskDistributor --> ConflictManager
```

### 2. Agent Architecture

```mermaid
classDiagram
    class BaseAgent {
        <<abstract>>
        #id: string
        #type: AgentType
        #state: AgentState
        #sessionId: string
        #logger: Logger
        +initialize(): Promise~void~
        +execute(task: ITask): Promise~IAgentResult~
        +terminate(): Promise~void~
        #onInitialize(): Promise~void~
        #prepareContext(task: ITask): Promise~IExecutionContext~
        #processResponse(response: ClaudeSDKResponse): Promise~string~
    }

    class ResearchAgent {
        +onInitialize(): Promise~void~
        +prepareContext(task: ITask): Promise~IExecutionContext~
        +processResponse(response: ClaudeSDKResponse): Promise~string~
    }

    class CodeAgent {
        -terminal: ITerminalSession
        +onInitialize(): Promise~void~
        +prepareContext(task: ITask): Promise~IExecutionContext~
        +processResponse(response: ClaudeSDKResponse): Promise~string~
        +executeCommand(cmd: string): Promise~ICommandResult~
    }

    class ReviewAgent {
        +onInitialize(): Promise~void~
        +analyzeCode(files: string[]): Promise~IReviewResult~
        +processResponse(response: ClaudeSDKResponse): Promise~string~
    }

    class TestAgent {
        -testRunner: ITestRunner
        +onInitialize(): Promise~void~
        +runTests(pattern: string): Promise~ITestResult~
        +processResponse(response: ClaudeSDKResponse): Promise~string~
    }

    BaseAgent <|-- ResearchAgent
    BaseAgent <|-- CodeAgent
    BaseAgent <|-- ReviewAgent
    BaseAgent <|-- TestAgent
```

### 3. Process Management Architecture

```mermaid
classDiagram
    class CLIProcessManager {
        -processPool: ProcessPool
        -sessionManager: SessionManager
        -circuitBreaker: CircuitBreaker
        -rateLimiter: RateLimiter
        +createSession(config: ISessionConfig): Promise~ClaudeSDKResponse~
        +execute(config: IExecutionConfig): Promise~ClaudeSDKResponse~
        +executeStreaming(config: IExecutionConfig): AsyncIterable~IStreamMessage~
        +shutdown(): Promise~void~
    }

    class TerminalPool {
        -terminals: Map~string, VirtualTerminal~
        -maxTerminals: number
        +allocate(agentId: string): Promise~ITerminalSession~
        +release(agentId: string): Promise~void~
        +getActiveCount(): number
    }

    class VirtualTerminal {
        -shell: ChildProcess
        -workingDirectory: string
        -env: Record~string, string~
        +execute(command: string): Promise~ICommandResult~
        +getOutput(): string[]
        +destroy(): Promise~void~
    }

    class SessionManager {
        -sessions: Map~string, ISessionInfo~
        +registerSession(id: string, info: ISessionInfo): void
        +getSession(id: string): ISessionInfo
        +removeSession(id: string): void
    }

    CLIProcessManager --> TerminalPool
    CLIProcessManager --> SessionManager
    TerminalPool --> VirtualTerminal
```

### 4. Repository Management Architecture

```mermaid
classDiagram
    class WorktreeManager {
        -baseRepo: string
        -worktrees: Map~string, Worktree~
        +createWorktree(agentId: string): Promise~Worktree~
        +syncWorktree(id: string): Promise~SyncResult~
        +mergeWorktree(id: string): Promise~MergeResult~
        +destroyWorktree(id: string): Promise~void~
    }

    class FileLockManager {
        -locks: Map~string, FileLock~
        -timeout: number
        +acquireLock(agentId: string, files: string[]): Promise~LockResult~
        +releaseLock(agentId: string, files: string[]): Promise~void~
        +checkLocks(files: string[]): Promise~LockStatus[]~
        +forceReleaseStaleLocks(): Promise~void~
    }

    class ConflictDetector {
        -astAnalyzer: ASTAnalyzer
        -semanticAnalyzer: SemanticAnalyzer
        +detectFileConflicts(changes: FileChange[]): Conflict[]
        +detectSemanticConflicts(changes: FileChange[]): SemanticConflict[]
        +predictConflicts(plan1: TaskPlan, plan2: TaskPlan): PredictedConflict[]
    }

    class MergeStrategy {
        <<interface>>
        +canHandle(conflict: Conflict): boolean
        +resolve(conflict: Conflict): Promise~Resolution~
    }

    WorktreeManager --> FileLockManager
    WorktreeManager --> ConflictDetector
    ConflictDetector --> MergeStrategy
```

## Data Flow Architecture

### 1. Task Execution Flow

```mermaid
sequenceDiagram
    participant User
    participant Orchestrator
    participant TaskDistributor
    participant MessageQueue
    participant Agent
    participant CLIProcess
    participant Worktree
    participant Repository

    User->>Orchestrator: Submit Task
    Orchestrator->>TaskDistributor: Analyze Task
    TaskDistributor->>TaskDistributor: Check Conflicts
    TaskDistributor->>MessageQueue: Publish Task Assignment
    MessageQueue->>Agent: Deliver Task
    Agent->>CLIProcess: Create Session
    Agent->>Worktree: Create Workspace
    Agent->>CLIProcess: Execute Task
    CLIProcess->>Claude API: Send Request
    Claude API->>CLIProcess: Return Response
    Agent->>Worktree: Apply Changes
    Agent->>Repository: Merge Changes
    Agent->>MessageQueue: Publish Result
    MessageQueue->>Orchestrator: Deliver Result
    Orchestrator->>User: Return Result
```

### 2. Conflict Resolution Flow

```mermaid
flowchart TB
    Start([Agent Requests File Lock])
    Check{Files Available?}
    Acquire[Acquire Lock]
    Conflict[Conflict Detected]
    Analyze[Analyze Conflict Type]
    
    FileConflict{File-level Conflict?}
    SemanticConflict{Semantic Conflict?}
    
    Wait[Wait for Lock Release]
    Alternative[Find Alternative Files]
    Collaborate[Request Collaboration]
    
    AutoMerge[Attempt Auto-merge]
    SemanticMerge[Semantic Merge]
    Manual[Escalate to Human]
    
    Success[Proceed with Task]
    End([Task Complete])
    
    Start --> Check
    Check -->|Yes| Acquire
    Check -->|No| Conflict
    
    Conflict --> Analyze
    Analyze --> FileConflict
    Analyze --> SemanticConflict
    
    FileConflict -->|Yes| Wait
    FileConflict -->|Yes| Alternative
    FileConflict -->|Yes| Collaborate
    
    SemanticConflict -->|Yes| AutoMerge
    SemanticConflict -->|Yes| SemanticMerge
    SemanticConflict -->|No| Manual
    
    Acquire --> Success
    Wait --> Check
    Alternative --> Success
    AutoMerge -->|Success| Success
    AutoMerge -->|Fail| Manual
    SemanticMerge -->|Success| Success
    SemanticMerge -->|Fail| Manual
    
    Success --> End
    Manual --> End
```

## Communication Architecture

### 1. Message Queue Pattern

```mermaid
graph LR
    subgraph Publishers
        O[Orchestrator]
        A1[Agent 1]
        A2[Agent 2]
    end
    
    subgraph Message Queue
        T1[task.* Topic]
        T2[agent.* Topic]
        T3[collab.* Topic]
        DLQ[Dead Letter Queue]
    end
    
    subgraph Subscribers
        AS1[Agent Sub 1]
        AS2[Agent Sub 2]
        OS[Orchestrator Sub]
    end
    
    O -->|task.assignment| T1
    A1 -->|agent.ready| T2
    A2 -->|collab.help_request| T3
    
    T1 -->|Subscribe| AS1
    T1 -->|Subscribe| AS2
    T2 -->|Subscribe| OS
    T3 -->|Subscribe| AS1
    T3 -->|Subscribe| AS2
    
    T1 -.->|Failed| DLQ
    T2 -.->|Failed| DLQ
    T3 -.->|Failed| DLQ
```

### 2. Session Management

```mermaid
stateDiagram-v2
    [*] --> Idle: Agent Created
    Idle --> Initializing: initialize()
    Initializing --> Ready: Session Created
    Ready --> Busy: Task Assigned
    Busy --> Ready: Task Complete
    Busy --> Error: Task Failed
    Error --> Ready: Error Handled
    Ready --> Terminated: terminate()
    Error --> Terminated: Unrecoverable
    Terminated --> [*]
```

## Deployment Architecture

### 1. Container Architecture (Optional)

```mermaid
graph TB
    subgraph Host
        subgraph Orchestrator Container
            ORC[Orchestrator Service]
            API[API Server]
        end
        
        subgraph Agent Containers
            subgraph Agent 1
                A1[Agent Process]
                T1[Terminal Session]
                W1[Worktree]
            end
            
            subgraph Agent 2
                A2[Agent Process]
                T2[Terminal Session]
                W2[Worktree]
            end
        end
        
        subgraph Infrastructure
            MQ[Message Queue]
            FS[Shared Storage]
            DB[State Database]
        end
    end
    
    ORC --> MQ
    A1 --> MQ
    A2 --> MQ
    
    W1 --> FS
    W2 --> FS
    
    ORC --> DB
    API --> DB
```

### 2. Resource Allocation

```mermaid
pie title Resource Allocation per Agent
    "CPU" : 25
    "Memory" : 30
    "Disk I/O" : 20
    "Network" : 15
    "Claude API" : 10
```

## Security Architecture

### 1. Permission Model

```mermaid
graph TB
    subgraph Agent Permissions
        R[Read Files]
        W[Write Files]
        E[Execute Commands]
        N[Network Access]
        C[Claude API Access]
    end
    
    subgraph Permission Profiles
        Research[Research Agent<br/>R: ✓ W: ✗ E: Limited N: ✓ C: ✓]
        Code[Code Agent<br/>R: ✓ W: ✓ E: ✓ N: ✗ C: ✓]
        Review[Review Agent<br/>R: ✓ W: ✗ E: ✗ N: ✗ C: ✓]
        Test[Test Agent<br/>R: ✓ W: ✗ E: ✓ N: ✗ C: ✓]
    end
    
    R --> Research
    R --> Code
    R --> Review
    R --> Test
    
    W --> Code
    
    E --> Code
    E --> Test
    
    N --> Research
    
    C --> Research
    C --> Code
    C --> Review
    C --> Test
```

## Performance Architecture

### 1. Caching Strategy

```mermaid
graph LR
    subgraph Cache Layers
        L1[Session Cache<br/>~10ms]
        L2[Memory Cache<br/>~50ms]
        L3[Disk Cache<br/>~200ms]
        L4[Claude API<br/>~2000ms]
    end
    
    Request -->|Check| L1
    L1 -->|Miss| L2
    L2 -->|Miss| L3
    L3 -->|Miss| L4
    
    L4 -->|Store| L3
    L3 -->|Store| L2
    L2 -->|Store| L1
```

### 2. Scalability Model

```mermaid
graph TB
    subgraph Horizontal Scaling
        O1[Orchestrator 1]
        O2[Orchestrator 2]
        LB[Load Balancer]
        
        LB --> O1
        LB --> O2
    end
    
    subgraph Agent Scaling
        AP[Agent Pool]
        AS[Auto Scaler]
        
        AS -->|Scale Up| AP
        AS -->|Scale Down| AP
    end
    
    subgraph Resource Scaling
        CPU[CPU: 1-16 cores]
        MEM[Memory: 4-64 GB]
        DISK[Disk: 10-500 GB]
    end
```

## Technology Stack

- **Runtime**: Node.js 18+
- **Language**: TypeScript 5+
- **CLI Framework**: Claude CLI SDK mode
- **Process Management**: Node.js child_process
- **Version Control**: Git with worktrees
- **Message Queue**: In-memory with persistence option
- **Testing**: Jest with 100% coverage
- **Monitoring**: Custom metrics collection
- **Logging**: Winston/Pino
- **Container**: Docker (optional)

## Architecture Principles

1. **Isolation First**: Every agent operates in complete isolation
2. **Fail Fast**: Early detection and handling of conflicts
3. **Eventual Consistency**: Agents converge to consistent state
4. **Observability**: Complete visibility into system operation
5. **Scalability**: Horizontal scaling of agents
6. **Resilience**: Circuit breakers and retry mechanisms
7. **Security**: Principle of least privilege