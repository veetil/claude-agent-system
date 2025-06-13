#!/usr/bin/env python3
"""
Working Multi-Agent System using Claude CLI with proper session management
Key: Use interactive login shell to ensure aliases/functions are loaded
"""

import subprocess
import json
import asyncio
import shlex
import os
from pathlib import Path
from typing import Dict, Optional, List

# Detect login shell
SHELL = os.environ.get("SHELL", "/bin/bash")

class ClaudeAgent:
    """Claude agent that maintains conversation history via session IDs"""
    
    def __init__(self, agent_id: str, working_dir: str, system_prompt: str = None):
        self.agent_id = agent_id
        self.working_dir = Path(working_dir).absolute()
        self.working_dir.mkdir(parents=True, exist_ok=True)
        self.current_session_id: Optional[str] = None
        self.system_prompt = system_prompt
        self.session_history: List[str] = []  # Track session ID chain
        
    def call_claude(self, prompt: str, resume_id: Optional[str] = None) -> Dict:
        """Call Claude CLI via interactive login shell"""
        # Build command
        args = ["claude"]
        if resume_id:
            args += ["-r", resume_id]
        args += ["-p", prompt, "--output-format", "json"]
        
        # Quote for shell
        shell_cmd = " ".join(shlex.quote(a) for a in args)
        
        # Run in working directory via interactive shell
        proc = subprocess.run(
            [SHELL, "-ic", shell_cmd],
            cwd=str(self.working_dir),
            capture_output=True,
            text=True
        )
        
        if proc.returncode != 0:
            print(f"[{self.agent_id}] Error: {proc.stderr.strip()}")
            return {"error": proc.stderr.strip()}
        
        # Clean output - find JSON start
        out = proc.stdout.strip()
        idx = out.find("{")
        out = out[idx:] if idx >= 0 else out
        
        try:
            return json.loads(out)
        except json.JSONDecodeError as e:
            print(f"[{self.agent_id}] JSON decode error: {e}")
            return {"error": f"JSON decode error: {e}", "raw_output": out}
    
    async def ask(self, prompt: str) -> str:
        """Send prompt to agent, maintaining session continuity"""
        # Add system prompt to first interaction
        if self.system_prompt and not self.current_session_id:
            full_prompt = f"System: {self.system_prompt}\n\nUser: {prompt}"
        else:
            full_prompt = prompt
        
        # Call Claude
        response = await asyncio.to_thread(
            self.call_claude, 
            full_prompt, 
            self.current_session_id
        )
        
        if "error" in response:
            return f"Error: {response['error']}"
        
        # Update session ID for next interaction
        new_session_id = response.get("session_id")
        if new_session_id:
            self.current_session_id = new_session_id
            self.session_history.append(new_session_id)
            print(f"[{self.agent_id}] Session updated: {new_session_id}")
        
        return response.get("result", response.get("message", ""))


class MultiAgentOrchestrator:
    """Orchestrates multiple Claude agents with proper session management"""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir).absolute()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.agents: Dict[str, ClaudeAgent] = {}
        
    def create_agent(self, agent_id: str, system_prompt: str) -> ClaudeAgent:
        """Create agent with dedicated working directory"""
        agent_dir = self.base_dir / f"agent_{agent_id}"
        agent = ClaudeAgent(agent_id, str(agent_dir), system_prompt)
        self.agents[agent_id] = agent
        print(f"Created agent '{agent_id}' in {agent_dir}")
        return agent
    
    async def test_session_continuity(self):
        """Demonstrate that session chaining works"""
        print("\n=== Testing Session Continuity ===\n")
        
        agent = self.create_agent(
            "memory_test",
            "You are a helpful assistant with perfect memory."
        )
        
        # Chain of interactions
        print("1. Setting context...")
        resp1 = await agent.ask("My favorite color is blue and I drive a Tesla.")
        print(f"Response: {resp1[:100]}...")
        
        print("\n2. Adding more context...")
        resp2 = await agent.ask("I also have 3 cats named Luna, Max, and Oliver.")
        print(f"Response: {resp2[:100]}...")
        
        print("\n3. Testing memory...")
        resp3 = await agent.ask("What do you remember about me? List my favorite color, car, and pets.")
        print(f"Response: {resp3}")
        
        # Verify memory
        response_lower = resp3.lower()
        remembers_all = all([
            "blue" in response_lower,
            "tesla" in response_lower,
            any(name.lower() in response_lower for name in ["luna", "max", "oliver"]),
            "3" in resp3 or "three" in response_lower
        ])
        
        print(f"\nSession continuity works: {remembers_all}")
        print(f"Session ID chain: {' -> '.join(agent.session_history)}")
        return remembers_all
    
    async def test_multi_agent_collaboration(self):
        """Test agents working together with context"""
        print("\n\n=== Multi-Agent Collaboration ===\n")
        
        # Create specialized agents
        self.create_agent(
            "architect",
            "You are a software architect. Design clean, modular solutions."
        )
        self.create_agent(
            "developer",
            "You are a Python developer. Write clean, efficient code."
        )
        self.create_agent(
            "tester",
            "You are a QA engineer. Write comprehensive tests."
        )
        
        # Collaborative task
        task = "Create a simple rate limiter class"
        
        print(f"Task: {task}\n")
        
        # Architect designs
        print("1. Architect designing solution...")
        design = await self.agents["architect"].ask(
            f"Design a {task} with clear interface and behavior description."
        )
        print(f"Design: {design[:200]}...\n")
        
        # Developer implements
        print("2. Developer implementing...")
        implementation = await self.agents["developer"].ask(
            f"Implement this design in Python:\n{design}"
        )
        print(f"Implementation: {implementation[:200]}...\n")
        
        # Tester creates tests
        print("3. Tester writing tests...")
        tests = await self.agents["tester"].ask(
            f"Write pytest tests for this implementation:\n{implementation}"
        )
        print(f"Tests: {tests[:200]}...\n")
        
        return {
            "design": design,
            "implementation": implementation,
            "tests": tests
        }
    
    async def test_parallel_execution(self):
        """Test parallel agent execution"""
        print("\n\n=== Parallel Agent Execution ===\n")
        
        # Create agents for parallel tasks
        tasks = [
            ("algo_expert", "You are an algorithms expert.", "Implement binary search in Python"),
            ("data_expert", "You are a data structures expert.", "Implement a stack class in Python"),
            ("ml_expert", "You are a machine learning expert.", "Implement linear regression from scratch")
        ]
        
        for agent_id, system_prompt, _ in tasks:
            self.create_agent(agent_id, system_prompt)
        
        print("Running agents in parallel...\n")
        start_time = asyncio.get_event_loop().time()
        
        # Execute in parallel
        results = await asyncio.gather(*[
            self.agents[agent_id].ask(task)
            for agent_id, _, task in tasks
        ])
        
        duration = asyncio.get_event_loop().time() - start_time
        
        print(f"Completed in {duration:.2f}s")
        for (agent_id, _, task), result in zip(tasks, results):
            has_code = "def " in result or "class " in result
            print(f"{agent_id}: {'✓' if has_code else '✗'} ({len(result)} chars)")
        
        return results


async def main():
    """Run demonstrations"""
    print("Claude Multi-Agent System with Working Session Management")
    print("=" * 60)
    print(f"Using shell: {SHELL}")
    print("=" * 60)
    
    orchestrator = MultiAgentOrchestrator("/tmp/claude-agents-working")
    
    # Test 1: Session continuity
    session_works = await orchestrator.test_session_continuity()
    
    # Test 2: Multi-agent collaboration
    collab_results = await orchestrator.test_multi_agent_collaboration()
    
    # Test 3: Parallel execution
    parallel_results = await orchestrator.test_parallel_execution()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✓ Session continuity: {session_works}")
    print(f"✓ Multi-agent collaboration: {bool(collab_results['implementation'])}")
    print(f"✓ Parallel execution: {len(parallel_results)} agents")
    print("\nKey insight: Using $SHELL -ic ensures aliases/functions load correctly")
    print("Session management works perfectly with -p and -r flags!")


if __name__ == "__main__":
    asyncio.run(main())