# Claude Code Multi-Agent System: Solution Architecture

## Executive Summary
Based on extensive testing and analysis, we've identified key limitations and developed solutions for building a multi-agent system with Claude Code SDK.

## Key Discovery: Session File Architecture
Each Claude session creates a `.jsonl` file in `~/.claude/projects/[project-path]/[session-id].jsonl`. When using `-r` (resume), it creates a NEW file with a NEW session ID rather than appending to the existing file.

### Session File Structure
```jsonl
{"type":"summary","summary":"Session summary","leafUuid":"..."}
{"type":"user","message":{"role":"user","content":"..."},"sessionId":"...","timestamp":"..."}
{"type":"assistant","message":{"role":"assistant","content":[...]},"sessionId":"...","timestamp":"..."}
```

## Architectural Recommendations

### 1. Hybrid Approach: CLI + Custom State Management
Since sessions create new files with each `-r`, we recommend:

```python
class MultiAgentOrchestrator:
    def __init__(self):
        self.session_chain = {}  # agent_id -> [session_ids]
        self.conversation_memory = {}  # agent_id -> conversation_history
        
    async def continue_conversation(self, agent_id, prompt):
        # Get the latest session ID for this agent
        latest_session = self.session_chain[agent_id][-1]
        
        # Include conversation context in prompt
        context = self.get_conversation_context(agent_id)
        full_prompt = f"{context}\n\nCurrent request: {prompt}"
        
        # Use CLI with latest session ID
        response = await self.claude_cli_call(full_prompt, resume=latest_session)
        
        # Extract new session ID from response
        new_session_id = response['session_id']
        self.session_chain[agent_id].append(new_session_id)
        
        return response
```

### 2. Session File Direct Access
For advanced use cases, directly read/write session files:

```python
class SessionFileManager:
    def __init__(self):
        self.session_dir = Path.home() / '.claude' / 'projects'
        
    def read_session(self, session_id):
        """Read full conversation from session file"""
        project_dir = self.get_project_dir()
        session_file = project_dir / f"{session_id}.jsonl"
        
        messages = []
        with open(session_file) as f:
            for line in f:
                entry = json.loads(line)
                if entry['type'] in ['user', 'assistant']:
                    messages.append(entry)
        return messages
        
    def merge_sessions(self, session_ids):
        """Merge multiple session histories"""
        all_messages = []
        for sid in session_ids:
            all_messages.extend(self.read_session(sid))
        return all_messages
```

### 3. Stateless Agent Design
Accept that each interaction creates a new session and design accordingly:

```python
class StatelessAgent:
    def __init__(self, role, system_prompt):
        self.role = role
        self.system_prompt = system_prompt
        self.memory = []  # External memory
        
    async def execute_task(self, task, context=None):
        # Build comprehensive prompt with all context
        prompt = self.build_contextual_prompt(task, context)
        
        # Single-shot execution
        response = await claude_code_query(
            prompt=prompt,
            system_prompt=self.system_prompt,
            max_turns=3,  # Allow multi-turn within single session
            permission_mode="acceptEdits"
        )
        
        # Store in external memory
        self.memory.append({
            'task': task,
            'response': response,
            'timestamp': time.time()
        })
        
        return response
```

## Recommended Architecture for Multi-Agent System

### Option 1: Coordinator Pattern (Recommended)
```
┌─────────────────┐
│   Coordinator   │ (Manages state & routing)
└────────┬────────┘
         │
    ┌────┴────┬────────┬────────┐
    │         │        │        │
┌───▼───┐ ┌──▼───┐ ┌──▼───┐ ┌──▼───┐
│Agent 1│ │Agent 2│ │Agent 3│ │Agent 4│
└───────┘ └──────┘ └──────┘ └──────┘
(Stateless specialized agents)
```

### Option 2: Message Queue Pattern
```
┌─────────────┐     ┌─────────────┐
│  Task Queue │────▶│ Result Queue│
└─────────────┘     └─────────────┘
       │                    ▲
       ▼                    │
   [Agents consume tasks and produce results]
```

### Option 3: Pipeline Pattern
```
Agent1 ──▶ Agent2 ──▶ Agent3 ──▶ Final Result
  │          │          │
  └──────────┴──────────┴─── Shared Context Store
```

## Implementation Guidelines

### 1. Agent Creation
```python
# Specialized agents with clear roles
agents = {
    'architect': Agent(
        system_prompt="You are a software architect. Focus on system design and structure.",
        tools=["Read", "Write"]
    ),
    'developer': Agent(
        system_prompt="You are a developer. Implement clean, efficient code.",
        tools=["Read", "Write", "Execute"]
    ),
    'tester': Agent(
        system_prompt="You are a QA engineer. Write comprehensive tests.",
        tools=["Read", "Write", "Execute"]
    ),
    'reviewer': Agent(
        system_prompt="You are a code reviewer. Find bugs and suggest improvements.",
        tools=["Read"]
    )
}
```

### 2. Task Distribution
```python
async def distribute_task(task, required_agents):
    results = {}
    context = SharedContext()
    
    for agent_name in required_agents:
        agent = agents[agent_name]
        
        # Each agent gets full context
        agent_prompt = f"""
        Task: {task}
        Previous work: {context.get_previous_work()}
        Your role: {agent.role}
        """
        
        result = await agent.execute(agent_prompt)
        results[agent_name] = result
        context.add_work(agent_name, result)
    
    return results
```

### 3. Error Handling
```python
async def resilient_agent_call(agent, task, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = await agent.execute(task)
            if result and not result.startswith("Error:"):
                return result
        except Exception as e:
            if attempt == max_retries - 1:
                return f"Failed after {max_retries} attempts: {str(e)}"
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

## Best Practices

1. **Accept Statelessness**: Design agents to be stateless, with context passed explicitly
2. **External Memory**: Maintain conversation history outside of Claude's session system
3. **Comprehensive Prompts**: Include all necessary context in each prompt
4. **Error Resilience**: Implement retry logic and fallback strategies
5. **Clear Agent Roles**: Define specific, non-overlapping responsibilities
6. **Async Execution**: Use async/await for concurrent agent operations
7. **Result Validation**: Verify agent outputs before passing to next stage

## Conclusion

While Claude Code SDK's session management creates new files for each interaction, this can be worked around by:
1. Tracking session ID chains
2. Managing context externally
3. Designing stateless agents
4. Using comprehensive prompts with full context

The multi-agent system should embrace these constraints rather than fight them, resulting in a more robust and scalable architecture.