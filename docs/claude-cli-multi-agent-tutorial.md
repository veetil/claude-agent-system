# Building a Multi-Agent System with Claude CLI: A Comprehensive Tutorial

## Table of Contents
1. [Introduction](#introduction)
2. [Core Concepts](#core-concepts)
3. [System Architecture](#system-architecture)
4. [Step-by-Step Implementation](#step-by-step-implementation)
5. [Advanced Features](#advanced-features)
6. [Best Practices](#best-practices)
7. [Complete Example](#complete-example)

## Introduction

This tutorial demonstrates how to build a Roo-style multi-agent system using Claude CLI, implementing:
- Specialized agents with focused roles
- Boomerang pattern (orchestrator → agent → orchestrator)
- JSON-based configuration
- Recursive agent spawning
- Coherent inter-agent communication

## Core Concepts

### 1. Agent as Process
Each agent is a separate Claude CLI process that:
- Receives tasks from the orchestrator
- Executes autonomously
- Returns results to the orchestrator

### 2. Boomerang Pattern
```
Orchestrator → Spawns Agent → Agent Executes → Returns Result → Orchestrator
```

### 3. Configuration-Driven Design
Agents are defined by JSON configuration files specifying:
- Capabilities
- Prompts
- Constraints
- Sub-agent permissions

## System Architecture

```
claude-roo/
├── orchestrator.py          # Main orchestrator
├── agents/
│   ├── base_agent.py       # Base agent class
│   ├── research_agent.py   # Specialized agents
│   ├── dev_agent.py
│   └── test_agent.py
├── config/
│   ├── agents/             # Agent definitions
│   │   ├── research.json
│   │   ├── developer.json
│   │   └── tester.json
│   └── prompts/            # Shared prompts
├── memory/                 # Shared memory
└── tasks/                  # Task history
```

## Step-by-Step Implementation

### Step 1: Base Agent Implementation

```python
# agents/base_agent.py
import subprocess
import json
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

class BaseAgent:
    """Base class for all Claude CLI agents"""
    
    def __init__(self, agent_id: str, config_path: str):
        self.agent_id = agent_id
        self.config = self._load_config(config_path)
        self.name = self.config['name']
        self.type = self.config['type']
        self.prompts = self.config['prompts']
        self.claude_model = self.config.get('claude_model', 'claude-3-opus-20240229')
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load agent configuration from JSON"""
        with open(config_path) as f:
            return json.load(f)
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task and return result (boomerang)"""
        try:
            # Build prompt from task and configuration
            prompt = self._build_prompt(task)
            
            # Execute via Claude CLI
            result = await self._call_claude(prompt, task.get('context', {}))
            
            # Process and return result
            return {
                'task_id': task['id'],
                'agent_id': self.agent_id,
                'status': 'completed',
                'result': result,
                'metadata': self._get_metadata()
            }
        except Exception as e:
            return {
                'task_id': task['id'],
                'agent_id': self.agent_id,
                'status': 'failed',
                'error': str(e)
            }
    
    def _build_prompt(self, task: Dict[str, Any]) -> str:
        """Build prompt from configuration and task"""
        system_prompt = self.prompts.get('system', '')
        task_template = self.prompts.get('task_template', '{description}')
        
        # Substitute variables
        prompt = task_template.format(
            description=task.get('description', ''),
            **task.get('parameters', {})
        )
        
        return f"{system_prompt}\n\n{prompt}"
    
    async def _call_claude(self, prompt: str, context: Dict[str, Any]) -> str:
        """Call Claude CLI and get response"""
        cmd = [
            'claude',
            prompt,
            '--model', self.claude_model,
            '--max-tokens', str(self.config.get('max_tokens', 4096))
        ]
        
        # Add context if provided
        if context:
            context_file = f"/tmp/context_{self.agent_id}.json"
            with open(context_file, 'w') as f:
                json.dump(context, f)
            cmd.extend(['--context-file', context_file])
        
        # Execute Claude CLI
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"Claude CLI failed: {stderr.decode()}")
        
        return stdout.decode()
    
    def _get_metadata(self) -> Dict[str, Any]:
        """Get agent metadata"""
        return {
            'agent_name': self.name,
            'agent_type': self.type,
            'model': self.claude_model
        }
```

### Step 2: Orchestrator Implementation

```python
# orchestrator.py
import asyncio
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import uuid
from datetime import datetime

from agents.base_agent import BaseAgent
from agents.research_agent import ResearchAgent
from agents.dev_agent import DevelopmentAgent
from agents.test_agent import TestAgent

class Orchestrator:
    """Central orchestrator for multi-agent system"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.agents: Dict[str, BaseAgent] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.results: Dict[str, Any] = {}
        self.memory = SharedMemory()
        self._load_agent_configs()
        
    def _load_agent_configs(self):
        """Load all agent configurations"""
        agent_configs = self.config_dir / "agents"
        
        # Map of agent types to classes
        agent_classes = {
            'research': ResearchAgent,
            'development': DevelopmentAgent,
            'testing': TestAgent
        }
        
        for config_file in agent_configs.glob("*.json"):
            with open(config_file) as f:
                config = json.load(f)
                agent_type = config['type']
                agent_id = config['id']
                
                # Create agent instance
                agent_class = agent_classes.get(agent_type, BaseAgent)
                agent = agent_class(agent_id, str(config_file))
                self.agents[agent_id] = agent
                
                print(f"Loaded agent: {config['name']} (type: {agent_type})")
    
    async def delegate_task(self, task_type: str, description: str, 
                          parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Delegate task to appropriate agent (boomerang pattern)"""
        # Create task
        task = {
            'id': str(uuid.uuid4()),
            'type': task_type,
            'description': description,
            'parameters': parameters or {},
            'created_at': datetime.now().isoformat()
        }
        
        # Find appropriate agent
        agent = self._select_agent(task_type)
        if not agent:
            return {
                'status': 'failed',
                'error': f'No agent found for task type: {task_type}'
            }
        
        print(f"Delegating task {task['id']} to {agent.name}")
        
        # Execute task (boomerang)
        result = await agent.execute(task)
        
        # Store result
        self.results[task['id']] = result
        
        # Update shared memory if needed
        if result['status'] == 'completed':
            self.memory.store(f"task_{task['id']}", result)
        
        return result
    
    def _select_agent(self, task_type: str) -> Optional[BaseAgent]:
        """Select agent based on task type"""
        for agent in self.agents.values():
            if agent.type == task_type:
                return agent
            # Check if agent has capability
            if task_type in agent.config.get('capabilities', []):
                return agent
        return None
    
    async def delegate_parallel(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Delegate multiple tasks in parallel"""
        coroutines = []
        for task in tasks:
            coro = self.delegate_task(
                task['type'],
                task['description'],
                task.get('parameters')
            )
            coroutines.append(coro)
        
        results = await asyncio.gather(*coroutines)
        return results
    
    async def spawn_sub_agent(self, parent_agent_id: str, sub_task: Dict[str, Any]) -> Dict[str, Any]:
        """Allow agent to spawn sub-agent (recursive pattern)"""
        parent_agent = self.agents.get(parent_agent_id)
        if not parent_agent:
            return {'status': 'failed', 'error': 'Parent agent not found'}
        
        # Check if parent can spawn sub-agents
        if not parent_agent.config.get('sub_agents', {}).get('allowed', False):
            return {'status': 'failed', 'error': 'Parent agent cannot spawn sub-agents'}
        
        # Check if sub-agent type is allowed
        allowed_types = parent_agent.config.get('sub_agents', {}).get('types', [])
        if sub_task['type'] not in allowed_types:
            return {'status': 'failed', 'error': f'Sub-agent type {sub_task["type"]} not allowed'}
        
        # Delegate to sub-agent
        return await self.delegate_task(
            sub_task['type'],
            sub_task['description'],
            sub_task.get('parameters')
        )

class SharedMemory:
    """Shared memory for inter-agent communication"""
    
    def __init__(self, storage_dir: str = "memory"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.cache: Dict[str, Any] = {}
    
    def store(self, key: str, value: Any):
        """Store value in shared memory"""
        self.cache[key] = value
        # Persist to disk
        file_path = self.storage_dir / f"{key}.json"
        with open(file_path, 'w') as f:
            json.dump(value, f, indent=2)
    
    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve value from shared memory"""
        if key in self.cache:
            return self.cache[key]
        
        # Try to load from disk
        file_path = self.storage_dir / f"{key}.json"
        if file_path.exists():
            with open(file_path) as f:
                value = json.load(f)
                self.cache[key] = value
                return value
        
        return None
    
    def search(self, pattern: str) -> List[str]:
        """Search for keys matching pattern"""
        import re
        regex = re.compile(pattern)
        matching_keys = []
        
        # Search in cache
        for key in self.cache:
            if regex.match(key):
                matching_keys.append(key)
        
        # Search on disk
        for file_path in self.storage_dir.glob("*.json"):
            key = file_path.stem
            if regex.match(key) and key not in matching_keys:
                matching_keys.append(key)
        
        return matching_keys
```

### Step 3: Specialized Agent Examples

```python
# agents/research_agent.py
from .base_agent import BaseAgent
import json
from typing import Dict, Any

class ResearchAgent(BaseAgent):
    """Specialized agent for research tasks"""
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute research task with specialized handling"""
        # Add research-specific context
        task['context'] = task.get('context', {})
        task['context']['search_depth'] = self.config.get('rules', {}).get('limits', {}).get('search_depth', 3)
        task['context']['require_citations'] = True
        
        # Call parent execute
        result = await super().execute(task)
        
        # Post-process research results
        if result['status'] == 'completed':
            result['result'] = self._format_research_output(result['result'])
        
        return result
    
    def _format_research_output(self, raw_output: str) -> Dict[str, Any]:
        """Format research output with structure"""
        # Parse Claude's response into structured format
        # This is a simplified example
        return {
            'summary': self._extract_section(raw_output, 'Summary'),
            'findings': self._extract_section(raw_output, 'Findings'),
            'sources': self._extract_sources(raw_output),
            'confidence': self._extract_confidence(raw_output)
        }
    
    def _extract_section(self, text: str, section: str) -> str:
        """Extract section from text"""
        import re
        pattern = f"## {section}\\s*\\n(.*?)(?=\\n## |$)"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else ""
    
    def _extract_sources(self, text: str) -> List[str]:
        """Extract sources from text"""
        import re
        sources = re.findall(r'\[(\d+)\]\s*(https?://[^\s]+)', text)
        return [url for _, url in sources]
    
    def _extract_confidence(self, text: str) -> str:
        """Extract confidence level"""
        import re
        match = re.search(r'Confidence:\s*(High|Medium|Low)', text, re.IGNORECASE)
        return match.group(1) if match else "Medium"
```

```python
# agents/dev_agent.py
from .base_agent import BaseAgent
import tempfile
import subprocess
from typing import Dict, Any

class DevelopmentAgent(BaseAgent):
    """Specialized agent for development tasks"""
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute development task"""
        # Check if we need to spawn sub-agents
        if task.get('parameters', {}).get('with_tests', False):
            # First execute main development task
            main_result = await super().execute(task)
            
            if main_result['status'] == 'completed':
                # Spawn test agent for the code
                test_task = {
                    'type': 'testing',
                    'description': f"Write tests for: {task['description']}",
                    'parameters': {
                        'code': main_result['result'],
                        'language': task.get('parameters', {}).get('language', 'python')
                    }
                }
                
                # This would be called through orchestrator in real implementation
                # test_result = await orchestrator.spawn_sub_agent(self.agent_id, test_task)
                
            return main_result
        
        return await super().execute(task)
    
    def _validate_code(self, code: str, language: str) -> Dict[str, Any]:
        """Validate generated code"""
        # Simple validation example
        validations = {
            'line_count': len(code.split('\n')),
            'has_docstrings': 'def ' in code and '"""' in code,
            'max_line_length': max(len(line) for line in code.split('\n'))
        }
        
        issues = []
        if validations['line_count'] > 500:
            issues.append("File exceeds 500 lines")
        if validations['max_line_length'] > 120:
            issues.append("Lines exceed 120 characters")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'metrics': validations
        }
```

### Step 4: Agent Configuration Files

```json
// config/agents/research.json
{
    "id": "research-001",
    "name": "Research Specialist",
    "type": "research",
    "description": "Specialized in deep research and information gathering",
    "claude_model": "claude-3-opus-20240229",
    "max_tokens": 4096,
    "temperature": 0.7,
    "capabilities": [
        "web_research",
        "fact_checking",
        "summarization",
        "comparative_analysis"
    ],
    "prompts": {
        "system": "You are a research specialist. Your role is to find accurate, comprehensive information on any topic. Always cite sources, verify facts, and provide balanced perspectives.",
        "task_template": "Research Task: {description}\n\nRequirements:\n- Depth: {depth}\n- Include at least 3 credible sources\n- Provide citations in [n] format\n- Structure output with Summary, Findings, and Sources sections\n- Include confidence level (High/Medium/Low)"
    },
    "rules": {
        "constraints": [
            {"max_query_length": 1000},
            {"require_citations": true}
        ],
        "limits": {
            "search_depth": 3,
            "max_sources": 10,
            "timeout_seconds": 300
        }
    },
    "sub_agents": {
        "allowed": true,
        "types": ["fact_checker", "summarizer"],
        "max_depth": 2
    }
}
```

```json
// config/agents/developer.json
{
    "id": "dev-001",
    "name": "Development Agent",
    "type": "development",
    "description": "Specialized in writing clean, maintainable code",
    "claude_model": "claude-3-opus-20240229",
    "max_tokens": 8192,
    "temperature": 0.3,
    "capabilities": [
        "code_generation",
        "refactoring",
        "debugging",
        "api_design"
    ],
    "prompts": {
        "system": "You are a senior software developer. Write clean, maintainable, well-tested code. Follow SOLID principles and clean code practices. Always include error handling and documentation.",
        "task_template": "Development Task: {description}\n\nLanguage: {language}\nFramework: {framework}\n\nRequirements:\n- Follow TDD approach\n- Include comprehensive docstrings\n- Handle errors gracefully\n- Keep functions under 50 lines\n- Ensure code is production-ready"
    },
    "rules": {
        "constraints": [
            {"max_file_lines": 500},
            {"max_function_lines": 50},
            {"require_docstrings": true}
        ],
        "limits": {
            "max_files": 10,
            "max_complexity": 10
        }
    },
    "sub_agents": {
        "allowed": true,
        "types": ["testing", "documentation", "code_reviewer"],
        "max_depth": 1
    }
}
```

### Step 5: Shared Prompt Blocks

```python
# config/prompts/shared_blocks.py
SHARED_PROMPTS = {
    "base_instructions": """
You are an AI agent in a multi-agent system. Follow these principles:
1. Complete your specific task and return results promptly
2. Maintain high quality standards
3. Communicate clearly and structure your outputs
4. Stay within your defined capabilities
5. When uncertain, ask for clarification
""",
    
    "error_handling": """
When encountering errors:
1. Provide clear error messages
2. Suggest potential solutions
3. Return partial results if possible
4. Log relevant debugging information
""",
    
    "output_format": """
Structure your output as:
## Summary
Brief overview of results

## Details
Comprehensive information

## Metadata
- Confidence: [High/Medium/Low]
- Processing Time: [estimated]
- Limitations: [if any]
""",
    
    "collaboration": """
When working with other agents:
1. Provide clear, structured outputs they can process
2. Include all necessary context
3. Use standard formats for data exchange
4. Document any assumptions made
"""
}
```

### Step 6: Running the System

```python
# main.py
import asyncio
from orchestrator import Orchestrator

async def main():
    # Initialize orchestrator
    orchestrator = Orchestrator()
    
    # Example 1: Single task delegation
    print("=== Research Task ===")
    research_result = await orchestrator.delegate_task(
        task_type="research",
        description="Research the latest developments in quantum computing",
        parameters={"depth": "comprehensive"}
    )
    print(f"Result: {research_result}")
    
    # Example 2: Development task with sub-agent
    print("\n=== Development Task ===")
    dev_result = await orchestrator.delegate_task(
        task_type="development",
        description="Create a Python function to calculate fibonacci numbers",
        parameters={
            "language": "python",
            "framework": "none",
            "with_tests": True
        }
    )
    print(f"Result: {dev_result}")
    
    # Example 3: Parallel task execution
    print("\n=== Parallel Tasks ===")
    tasks = [
        {
            "type": "research",
            "description": "Research best practices for API design",
            "parameters": {"depth": "moderate"}
        },
        {
            "type": "development",
            "description": "Create a REST API endpoint for user registration",
            "parameters": {"language": "python", "framework": "fastapi"}
        }
    ]
    
    parallel_results = await orchestrator.delegate_parallel(tasks)
    for i, result in enumerate(parallel_results):
        print(f"Task {i+1} Result: {result['status']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Advanced Features

### 1. Dynamic Agent Loading

```python
class DynamicAgentLoader:
    """Load agents dynamically from plugins"""
    
    def load_agent_plugin(self, plugin_path: str) -> BaseAgent:
        import importlib.util
        spec = importlib.util.spec_from_file_location("agent_plugin", plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find agent class in module
        for name, obj in vars(module).items():
            if isinstance(obj, type) and issubclass(obj, BaseAgent) and obj != BaseAgent:
                return obj
        
        raise ValueError("No agent class found in plugin")
```

### 2. Agent Communication Protocol

```python
class AgentMessage:
    """Standard message format for inter-agent communication"""
    
    def __init__(self, from_agent: str, to_agent: str, 
                 message_type: str, payload: Any):
        self.id = str(uuid.uuid4())
        self.timestamp = datetime.now().isoformat()
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.type = message_type
        self.payload = payload
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'timestamp': self.timestamp,
            'from_agent': self.from_agent,
            'to_agent': self.to_agent,
            'type': self.type,
            'payload': self.payload
        }
```

### 3. Context Window Management

```python
class ContextManager:
    """Manage context for Claude CLI calls"""
    
    def __init__(self, max_tokens: int = 100000):
        self.max_tokens = max_tokens
        self.token_counter = ClaudeTokenCounter()
    
    def prepare_context(self, messages: List[Dict[str, Any]], 
                       max_history: int = 10) -> str:
        """Prepare context within token limits"""
        # Take most recent messages
        recent_messages = messages[-max_history:]
        
        # Build context
        context_parts = []
        total_tokens = 0
        
        for message in reversed(recent_messages):
            message_text = json.dumps(message)
            tokens = self.token_counter.count(message_text)
            
            if total_tokens + tokens > self.max_tokens:
                break
                
            context_parts.insert(0, message_text)
            total_tokens += tokens
        
        return "\n".join(context_parts)
```

### 4. Monitoring and Observability

```python
class AgentMonitor:
    """Monitor agent performance and health"""
    
    def __init__(self):
        self.metrics = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'average_response_time': 0,
            'token_usage': {}
        }
    
    async def track_execution(self, agent_id: str, task_id: str,
                            execution_func):
        """Track agent execution metrics"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            result = await execution_func()
            self.metrics['tasks_completed'] += 1
            
            # Update response time
            duration = asyncio.get_event_loop().time() - start_time
            self._update_average_response_time(duration)
            
            return result
            
        except Exception as e:
            self.metrics['tasks_failed'] += 1
            raise
    
    def get_agent_health(self, agent_id: str) -> Dict[str, Any]:
        """Get health metrics for an agent"""
        success_rate = self.metrics['tasks_completed'] / (
            self.metrics['tasks_completed'] + self.metrics['tasks_failed']
        )
        
        return {
            'status': 'healthy' if success_rate > 0.8 else 'degraded',
            'success_rate': success_rate,
            'average_response_time': self.metrics['average_response_time'],
            'total_tasks': self.metrics['tasks_completed'] + self.metrics['tasks_failed']
        }
```

## Best Practices

### 1. Agent Design Principles

1. **Single Responsibility**: Each agent should have one clear purpose
2. **Stateless Execution**: Agents should not maintain state between tasks
3. **Fail Fast**: Return errors quickly rather than hanging
4. **Defensive Programming**: Validate inputs and handle edge cases

### 2. Prompt Engineering

1. **Clear Instructions**: Be explicit about expected outputs
2. **Examples**: Include examples in prompts when possible
3. **Constraints**: Specify clear constraints and limitations
4. **Format Specifications**: Define output formats precisely

### 3. Error Handling

```python
class AgentError(Exception):
    """Base exception for agent errors"""
    pass

class TaskValidationError(AgentError):
    """Raised when task validation fails"""
    pass

class AgentTimeoutError(AgentError):
    """Raised when agent execution times out"""
    pass

class SubAgentSpawnError(AgentError):
    """Raised when sub-agent spawning fails"""
    pass

# Usage in agents
async def execute_with_retry(agent, task, max_retries=3):
    """Execute task with retry logic"""
    for attempt in range(max_retries):
        try:
            return await agent.execute(task)
        except AgentTimeoutError:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
        except TaskValidationError:
            # Don't retry validation errors
            raise
```

### 4. Testing Strategies

```python
# tests/test_orchestrator.py
import pytest
from unittest.mock import Mock, patch
from orchestrator import Orchestrator

@pytest.mark.asyncio
async def test_task_delegation():
    """Test basic task delegation"""
    orchestrator = Orchestrator()
    
    # Mock Claude CLI call
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.stdout = "Test result"
        mock_run.return_value.returncode = 0
        
        result = await orchestrator.delegate_task(
            "research",
            "Test research task"
        )
        
        assert result['status'] == 'completed'
        assert 'Test result' in str(result['result'])

@pytest.mark.asyncio
async def test_parallel_execution():
    """Test parallel task execution"""
    orchestrator = Orchestrator()
    
    tasks = [
        {"type": "research", "description": "Task 1"},
        {"type": "development", "description": "Task 2"}
    ]
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.stdout = "Result"
        mock_run.return_value.returncode = 0
        
        results = await orchestrator.delegate_parallel(tasks)
        
        assert len(results) == 2
        assert all(r['status'] == 'completed' for r in results)
```

## Complete Example

### Multi-Stage Research and Development Pipeline

```python
async def research_and_develop_feature(orchestrator: Orchestrator, 
                                     feature_description: str):
    """Complete pipeline from research to implementation"""
    
    print(f"Starting pipeline for: {feature_description}")
    
    # Stage 1: Research
    research_result = await orchestrator.delegate_task(
        "research",
        f"Research best practices and patterns for: {feature_description}",
        {"depth": "comprehensive"}
    )
    
    if research_result['status'] != 'completed':
        print("Research failed")
        return
    
    research_output = research_result['result']
    
    # Stage 2: Design
    design_result = await orchestrator.delegate_task(
        "development",
        f"Create a technical design based on research: {research_output['summary']}",
        {
            "type": "design",
            "language": "python",
            "include_diagrams": True
        }
    )
    
    # Stage 3: Implementation
    implementation_tasks = []
    
    # Break down into components (mock example)
    components = ["api", "database", "frontend"]
    
    for component in components:
        task = {
            "type": "development",
            "description": f"Implement {component} for {feature_description}",
            "parameters": {
                "language": "python" if component != "frontend" else "javascript",
                "design": design_result['result'],
                "with_tests": True
            }
        }
        implementation_tasks.append(task)
    
    # Execute implementations in parallel
    impl_results = await orchestrator.delegate_parallel(implementation_tasks)
    
    # Stage 4: Integration Testing
    integration_result = await orchestrator.delegate_task(
        "testing",
        "Create integration tests for all components",
        {
            "components": [r['result'] for r in impl_results if r['status'] == 'completed'],
            "test_type": "integration"
        }
    )
    
    # Stage 5: Documentation
    doc_result = await orchestrator.delegate_task(
        "documentation",
        f"Create comprehensive documentation for {feature_description}",
        {
            "include_api_docs": True,
            "include_user_guide": True,
            "components": impl_results
        }
    )
    
    print("Pipeline completed!")
    return {
        "research": research_result,
        "design": design_result,
        "implementation": impl_results,
        "testing": integration_result,
        "documentation": doc_result
    }

# Run the pipeline
if __name__ == "__main__":
    orchestrator = Orchestrator()
    result = asyncio.run(
        research_and_develop_feature(
            orchestrator,
            "Real-time collaborative editing feature"
        )
    )
```

## Conclusion

This tutorial demonstrates how to build a sophisticated multi-agent system using Claude CLI that implements:

1. **Specialized Agents**: Each with focused capabilities
2. **Boomerang Pattern**: Clean task delegation and return
3. **JSON Configuration**: Flexible agent definitions
4. **Recursive Spawning**: Agents can create sub-agents
5. **Coherent Communication**: Structured message passing
6. **Shared Memory**: For inter-agent knowledge sharing
7. **Parallel Execution**: For improved performance

The system is extensible, maintainable, and follows the principles demonstrated in Roo-Code while being adapted for direct Claude CLI usage.

Key takeaways:
- Use subprocess for Claude CLI integration
- Implement proper error handling and retries
- Structure prompts carefully for consistent outputs
- Monitor agent performance and health
- Test thoroughly with mocks and integration tests

This architecture can be extended with additional features like:
- WebSocket-based real-time updates
- Distributed agent execution across machines
- Advanced scheduling and prioritization
- Machine learning for agent selection
- Persistent task queues with Redis/RabbitMQ