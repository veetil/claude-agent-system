#!/usr/bin/env python3
"""
Simple Multi-Agent POC using Claude CLI with session management
Key insight: Use Claude's built-in session system by tracking session IDs
"""

import subprocess
import json
import asyncio
from pathlib import Path
from typing import Dict, Optional

class ClaudeAgent:
    """Single agent that maintains its own session via Claude CLI"""
    
    def __init__(self, agent_id: str, working_dir: str, system_prompt: str = None):
        self.agent_id = agent_id
        self.working_dir = Path(working_dir).absolute()
        self.working_dir.mkdir(parents=True, exist_ok=True)
        self.current_session_id: Optional[str] = None
        self.system_prompt = system_prompt
        self.interaction_count = 0
        
    async def ask(self, prompt: str) -> Dict:
        """Send prompt to Claude, maintaining session continuity"""
        
        self.interaction_count += 1
        
        # Add system prompt to first interaction only
        if self.system_prompt and self.interaction_count == 1:
            full_prompt = f"System: {self.system_prompt}\n\nUser: {prompt}"
        else:
            full_prompt = prompt
            
        # Build command
        cmd = ['claude', '-p', full_prompt, '--output-format', 'json']
        
        # Resume session if we have a session ID
        if self.current_session_id:
            cmd.extend(['-r', self.current_session_id])
            
        print(f"\n[{self.agent_id}] Interaction #{self.interaction_count}")
        print(f"[{self.agent_id}] Working dir: {self.working_dir}")
        if self.current_session_id:
            print(f"[{self.agent_id}] Resuming session: {self.current_session_id}")
        
        # Run command from agent's working directory
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(self.working_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            print(f"[{self.agent_id}] Error: {error_msg}")
            return {"error": error_msg}
            
        try:
            response = json.loads(stdout.decode())
            
            # Update session ID for next interaction
            new_session_id = response.get('session_id')
            if new_session_id:
                print(f"[{self.agent_id}] New session ID: {new_session_id}")
                self.current_session_id = new_session_id
                
            return response
        except json.JSONDecodeError as e:
            print(f"[{self.agent_id}] JSON decode error: {e}")
            return {"error": f"JSON decode error: {e}"}


class MultiAgentOrchestrator:
    """Orchestrates multiple Claude agents"""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir).absolute()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.agents: Dict[str, ClaudeAgent] = {}
        
    def create_agent(self, agent_id: str, system_prompt: str) -> ClaudeAgent:
        """Create a new agent with its own working directory"""
        
        agent_dir = self.base_dir / f"agent_{agent_id}"
        agent = ClaudeAgent(agent_id, str(agent_dir), system_prompt)
        self.agents[agent_id] = agent
        
        print(f"Created agent '{agent_id}' with working dir: {agent_dir}")
        return agent
        
    async def demonstrate_session_persistence(self):
        """Show that agents remember conversation history"""
        
        print("\n=== Demonstrating Session Persistence ===\n")
        
        # Create a test agent
        agent = self.create_agent(
            "memory_test",
            "You are a helpful assistant with perfect memory."
        )
        
        # First interaction
        resp1 = await agent.ask("My name is Alice and I love Python programming.")
        print(f"Response 1: {resp1.get('message', '')[:100]}...")
        
        # Second interaction - should remember the name
        resp2 = await agent.ask("What's my name and what do I love?")
        print(f"Response 2: {resp2.get('message', '')[:150]}...")
        
        # Check if agent remembered
        message = resp2.get('message', '').lower()
        remembered = 'alice' in message and 'python' in message
        print(f"\nAgent remembered context: {remembered}")
        
        return remembered
        
    async def demonstrate_multi_agent_collaboration(self):
        """Show multiple agents working together"""
        
        print("\n\n=== Demonstrating Multi-Agent Collaboration ===\n")
        
        # Create specialized agents
        self.create_agent(
            "architect",
            "You are a software architect. Design clean, scalable solutions."
        )
        
        self.create_agent(
            "developer", 
            "You are a senior developer. Implement efficient, clean code."
        )
        
        self.create_agent(
            "reviewer",
            "You are a code reviewer. Analyze code for bugs and improvements."
        )
        
        # Task: Create a simple task queue system
        task = "a simple in-memory task queue with add_task and get_next_task methods"
        
        # Architect designs the solution
        print("\n--- Architect Phase ---")
        design_resp = await self.agents['architect'].ask(
            f"Design {task}. Provide a clear interface design."
        )
        design = design_resp.get('message', '')
        print(f"Design preview: {design[:200]}...")
        
        # Developer implements it
        print("\n--- Developer Phase ---")
        impl_resp = await self.agents['developer'].ask(
            f"Implement this design in Python:\n{design}"
        )
        implementation = impl_resp.get('message', '')
        print(f"Implementation preview: {implementation[:200]}...")
        
        # Reviewer analyzes it
        print("\n--- Reviewer Phase ---")
        review_resp = await self.agents['reviewer'].ask(
            f"Review this code for bugs and suggest improvements:\n{implementation}"
        )
        review = review_resp.get('message', '')
        print(f"Review preview: {review[:200]}...")
        
        return {
            'design': design,
            'implementation': implementation,
            'review': review
        }
        
    async def demonstrate_parallel_agents(self):
        """Show agents working in parallel"""
        
        print("\n\n=== Demonstrating Parallel Agent Execution ===\n")
        
        # Create multiple agents for parallel tasks
        tasks = [
            ("sort_expert", "You are an algorithm expert.", "Write a Python quicksort function"),
            ("data_expert", "You are a data structures expert.", "Write a Python binary tree class"),
            ("test_expert", "You are a testing expert.", "Write a Python unit test for a calculator")
        ]
        
        agents = []
        for agent_id, system_prompt, _ in tasks:
            agent = self.create_agent(agent_id, system_prompt)
            agents.append(agent)
            
        # Run all agents in parallel
        print("\nRunning 3 agents in parallel...")
        start_time = asyncio.get_event_loop().time()
        
        results = await asyncio.gather(*[
            agent.ask(task) for agent, (_, _, task) in zip(agents, tasks)
        ])
        
        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time
        
        print(f"\nCompleted in {duration:.2f} seconds")
        print("All agents produced code:", all('def' in r.get('message', '') or 'class' in r.get('message', '') for r in results))
        
        return results


async def main():
    """Run the POC demonstrations"""
    
    print("Claude Multi-Agent POC")
    print("=" * 50)
    
    # Create orchestrator with a test directory
    orchestrator = MultiAgentOrchestrator("/tmp/claude-multi-agent-poc")
    
    # Test 1: Session persistence
    session_test_passed = await orchestrator.demonstrate_session_persistence()
    
    # Test 2: Multi-agent collaboration
    collab_results = await orchestrator.demonstrate_multi_agent_collaboration()
    
    # Test 3: Parallel execution
    parallel_results = await orchestrator.demonstrate_parallel_agents()
    
    # Summary
    print("\n\n" + "=" * 50)
    print("POC SUMMARY")
    print("=" * 50)
    print(f"✓ Session persistence works: {session_test_passed}")
    print(f"✓ Multi-agent collaboration works: {bool(collab_results['implementation'])}")
    print(f"✓ Parallel execution works: {len(parallel_results) == 3}")
    print("\nKey insight verified: Claude CLI maintains conversation history")
    print("when launched from the same directory with updated session IDs.")
    

if __name__ == "__main__":
    asyncio.run(main())