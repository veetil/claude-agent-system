# Simplified Multi-Agent Solution with Claude CLI

## Key Insight
Session persistence in Claude CLI is simple:
1. Sessions are tied to the folder where CLI is launched
2. Each `-r` (resume) creates a new session file but maintains conversation history
3. Just update the session ID with each interaction
4. Claude manages the conversation history internally

## Why This Matters
- We CANNOT directly input message history to Claude
- There's no API to inject conversation context
- Therefore, using Claude's session system is the ONLY way to maintain context

## Simple Implementation

### Agent Manager
```python
class ClaudeAgent:
    def __init__(self, agent_id: str, working_dir: str, system_prompt: str = None):
        self.agent_id = agent_id
        self.working_dir = Path(working_dir).absolute()
        self.current_session_id = None
        self.system_prompt = system_prompt
        
    async def ask(self, prompt: str) -> dict:
        """Send prompt to agent, maintaining session continuity"""
        
        # Build command
        cmd = ['claude', '-p', prompt, '--output-format', 'json']
        
        # Add system prompt to first message if needed
        if self.system_prompt and not self.current_session_id:
            prompt = f"System: {self.system_prompt}\n\n{prompt}"
        
        # Resume previous session if exists
        if self.current_session_id:
            cmd.extend(['-r', self.current_session_id])
        
        # Run from agent's working directory (CRITICAL!)
        result = subprocess.run(
            cmd,
            cwd=self.working_dir,  # This ensures session persistence
            capture_output=True,
            text=True
        )
        
        response = json.loads(result.stdout)
        
        # Update session ID for next call
        self.current_session_id = response.get('session_id')
        
        return response
```

### Multi-Agent Orchestrator
```python
class MultiAgentSystem:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.agents = {}
        
    def create_agent(self, agent_id: str, system_prompt: str) -> ClaudeAgent:
        """Create agent with its own working directory"""
        
        # Each agent gets its own folder for session isolation
        agent_dir = self.base_dir / f"agent_{agent_id}"
        agent_dir.mkdir(exist_ok=True)
        
        agent = ClaudeAgent(
            agent_id=agent_id,
            working_dir=agent_dir,
            system_prompt=system_prompt
        )
        
        self.agents[agent_id] = agent
        return agent
        
    async def collaborate(self, task: str):
        """Have agents work together on a task"""
        
        # Example: Designer -> Developer -> Tester flow
        design = await self.agents['designer'].ask(f"Design solution for: {task}")
        
        code = await self.agents['developer'].ask(
            f"Implement this design: {design['message']}"
        )
        
        tests = await self.agents['tester'].ask(
            f"Write tests for this code: {code['message']}"
        )
        
        return {
            'design': design,
            'implementation': code,
            'tests': tests
        }
```

## Usage Example
```python
# Initialize system
system = MultiAgentSystem("/Users/mi/Projects/claude-agents")

# Create specialized agents
system.create_agent("designer", "You are a software architect. Focus on clean design.")
system.create_agent("developer", "You are a senior developer. Write efficient code.")
system.create_agent("tester", "You are a QA engineer. Write comprehensive tests.")

# Agents maintain their own conversation history
designer = system.agents['designer']

# First interaction
response1 = await designer.ask("Design a user authentication system")
# Session ID: abc123

# Second interaction (continues conversation)
response2 = await designer.ask("Add 2FA to the design")
# Uses session abc123, returns new session def456

# Third interaction (remembers all context)
response3 = await designer.ask("What security measures have we included?")
# Uses session def456, Claude remembers the entire conversation
```

## Critical Points

1. **Folder = Session Context**: Each agent MUST run from the same folder to maintain sessions
2. **Session ID Chain**: Each interaction returns a new session ID that must be used next time
3. **No Manual History**: We cannot inject conversation history - must use Claude's sessions
4. **Automatic Context**: Claude automatically includes all previous messages in the session

## Benefits of This Approach

✅ Simple - Just track session IDs
✅ Reliable - Claude manages conversation history
✅ Scalable - Each agent has isolated context
✅ Natural - Works with Claude's design, not against it

## Implementation Checklist

- [ ] Create dedicated folders for each agent
- [ ] Always run CLI from agent's folder (cwd parameter)
- [ ] Track and update session IDs after each call
- [ ] Include system prompts in first message only
- [ ] Let Claude handle conversation memory internally