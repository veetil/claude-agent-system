# Roo-Code Multi-Agent System Analysis

## Overview

Roo-Code implements a sophisticated multi-agent architecture where each `Task` instance operates as an autonomous agent. This document analyzes how Roo-Code achieves the goals outlined in the readme.md.

## 1. Specialized Agents

### Implementation in Roo-Code

Roo-Code implements specialized agents through its **Mode System**:

```typescript
// Built-in specialized modes (agents)
- Code Mode: Development-focused agent
- Architect Mode: System design agent  
- Ask Mode: Interactive Q&A agent
- Debug Mode: Debugging specialist agent
```

**Key Pattern**: Each mode acts as a specialized agent with:
- Custom system prompts
- Specific tool permissions
- Focused capabilities
- Mode-specific behavior

### How It Works

1. **Mode Configuration** (`src/shared/modes.ts`):
```typescript
export const AVAILABLE_MODES: RooModes = {
    "code": {
        slug: "code",
        name: "Code",
        description: "General purpose coding mode",
        alwaysAllowReadOnlyMode: false,
        alwaysAllowBrowser: true,
        alwaysAllowCommand: true
    },
    // ... other modes
}
```

2. **Dynamic Specialization**:
- Tasks can switch modes during execution
- Each mode has different permissions and capabilities
- Custom modes can be defined by users

## 2. JSON-Based Agent Configuration

### Implementation in Roo-Code

Roo-Code uses JSON configurations for:

1. **Custom Modes** (`config/CustomModesManager.ts`):
```typescript
interface CustomMode {
    slug: string
    name: string
    roleDefinition: string
    customInstructions?: string
    disabledTools?: string[]
    temperature?: number
}
```

2. **Provider Settings** (JSON-based API configurations)
3. **MCP Server Configurations** (external tool integrations)

### Configuration Examples

```json
// Custom mode definition
{
    "slug": "researcher",
    "name": "Research Agent",
    "roleDefinition": "You are a research specialist...",
    "customInstructions": "Always cite sources...",
    "disabledTools": ["execute_command"],
    "temperature": 0.7
}
```

## 3. Comprehensive Prompting Blocks

### Implementation in Roo-Code

Roo-Code implements shared prompting through:

1. **System Prompt Generation** (`src/core/webview/generateSystemPrompt.ts`):
```typescript
function generateSystemPrompt(task: Task): string {
    const sections = [
        SYSTEM_INFO,
        OBJECTIVE,
        CAPABILITIES,
        RULES,
        MODE_SPECIFIC_INSTRUCTIONS,
        CUSTOM_INSTRUCTIONS
    ]
    return sections.join('\n\n')
}
```

2. **Prompt Sections** (`src/core/prompts/sections/`):
- `capabilities.ts`: Tool capabilities
- `modes.ts`: Mode-specific instructions  
- `rules.ts`: Global behavioral rules
- `system-info.ts`: Environment context

### Shared Prompt Architecture

All agents share core prompt blocks:
- System information
- Tool usage guidelines
- Markdown formatting rules
- Error handling instructions

Mode-specific agents extend these with specialized instructions.

## 4. Boomerang Mode Implementation

### How Roo-Code Implements Boomerang Pattern

1. **Task Spawning and Return**:
```typescript
// Parent task spawns child
async newTaskTool(task: Task, instruction: string) {
    const childTask = await provider.initClineWithTask(instruction)
    task.isPaused = true  // Parent waits
    task.emit("taskSpawned", childTask.taskId)
}

// Child completes and returns
async exitCommand() {
    if (parentTask) {
        parentTask.isPaused = false  // Parent resumes
        parentTask.emit("taskUnpaused")
    }
}
```

2. **Result Propagation**:
- Child tasks complete their work
- Results are saved to conversation history
- Parent task resumes with child's results available

## 5. Agent Hierarchy and Sub-Folders

### Implementation Pattern

Roo-Code organizes agents through:

1. **Task Stack** (`clineStack`):
```typescript
// Hierarchical task management
const taskStack: Task[] = []
// Current task is at top of stack
// Parent tasks lower in stack
```

2. **File System Organization**:
```
.roo/tasks/
├── task_123/
│   ├── conversation.json
│   └── api_conversation.json
├── task_456/ (sub-task)
│   ├── conversation.json
│   └── api_conversation.json
```

## 6. Optional Agent-to-Agent Communication

### Implementation in Roo-Code

1. **Direct Communication**: Not implemented (follows orchestrator pattern)

2. **Indirect Communication via Orchestrator**:
- Parent-child task relationships
- Shared file system access
- Event propagation

3. **Configuration for Communication**:
```typescript
// MCP servers enable external agent communication
interface McpServer {
    command: string
    args?: string[]
    env?: Record<string, string>
}
```

## 7. Coherent Communication Between Agents

### How Roo-Code Ensures Coherence

1. **Context Preservation**:
```typescript
// Context passed to child tasks
const contextForChild = {
    parentTaskId: parent.taskId,
    workingDirectory: parent.cwd,
    fileContext: parent.getRelevantFiles()
}
```

2. **Conversation History**:
- All task conversations saved
- Context can be inherited from parent
- File modifications tracked globally

3. **Event System**:
```typescript
// Coherent event propagation
task.on("taskCompleted", (result) => {
    parentTask.handleChildCompletion(result)
})
```

## Architecture Patterns for Multi-Agent Systems

### 1. Task as Agent Pattern

Each Task instance is a complete agent with:
- Autonomous decision-making
- Tool execution capabilities  
- State management
- Error recovery

### 2. Hierarchical Orchestration

```
Orchestrator (ClineProvider)
    ├── Task A (Research Agent)
    │   ├── Task A.1 (Web Search)
    │   └── Task A.2 (Summarizer)
    └── Task B (Development Agent)
        ├── Task B.1 (Test Writer)
        └── Task B.2 (Code Generator)
```

### 3. Mode-Based Specialization

Agents specialize through modes rather than classes:
- Runtime specialization
- Dynamic capability adjustment
- Shared core functionality

### 4. Tool-Based Capabilities

All agent actions expressed as tools:
- Modular capabilities
- Permission-based access
- Extensible through MCP

## Key Takeaways

1. **Task = Agent**: Each Task instance is an autonomous agent
2. **Modes = Specialization**: Modes provide agent specialization
3. **Stack = Hierarchy**: Task stack implements agent hierarchy
4. **Events = Communication**: Event system enables coherent communication
5. **Tools = Capabilities**: Tool system defines agent capabilities
6. **JSON = Configuration**: JSON configs for modes and settings

This architecture enables Roo-Code to function as a powerful multi-agent system while maintaining simplicity and extensibility.