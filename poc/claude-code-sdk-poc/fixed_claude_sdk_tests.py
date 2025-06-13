#!/usr/bin/env python3
"""
Fixed Claude Code SDK Tests with Proper Error Handling and Solutions
"""

import asyncio
import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
import os
# Set PATH to include claude-code
os.environ['PATH'] = '/opt/homebrew/lib/node_modules/@anthropic-ai/claude-code:' + os.environ.get('PATH', '')

from claude_code_sdk import query, ClaudeCodeOptions
from claude_code_sdk._errors import (
    CLIJSONDecodeError,
    CLINotFoundError,
    CLIConnectionError,
    ProcessError
)

class SessionManager:
    """Custom session management since SDK doesn't persist sessions"""
    
    def __init__(self):
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
    
    def save_context(self, agent_id: str, prompt: str, response: str):
        if agent_id not in self.conversations:
            self.conversations[agent_id] = []
        self.conversations[agent_id].append({
            'timestamp': time.time(),
            'prompt': prompt,
            'response': response
        })
    
    def get_context(self, agent_id: str) -> str:
        """Get formatted context for an agent"""
        if agent_id not in self.conversations:
            return ""
        
        context_parts = []
        for entry in self.conversations[agent_id][-5:]:  # Last 5 exchanges
            context_parts.append(f"User: {entry['prompt']}")
            context_parts.append(f"Assistant: {entry['response']}")
        
        return "\n\n".join(context_parts)


class ImprovedClaudeAgent:
    """Improved Claude agent with error handling and session management"""
    
    def __init__(self, agent_id: str, system_prompt: str = None, session_manager: SessionManager = None):
        self.agent_id = agent_id
        self.system_prompt = system_prompt
        self.session_manager = session_manager or SessionManager()
        self.message_history = []
        
    async def ask(self, prompt: str, max_turns: int = 1, include_context: bool = False) -> str:
        """Send prompt with proper error handling"""
        
        # Build prompt with context if needed
        full_prompt = prompt
        if include_context:
            context = self.session_manager.get_context(self.agent_id)
            if context:
                full_prompt = f"Previous conversation:\n{context}\n\nCurrent request: {prompt}"
        
        # Configure options with proper permissions
        options = ClaudeCodeOptions(
            system_prompt=self.system_prompt,
            max_turns=max_turns,
            permission_mode="acceptEdits",  # Auto-accept file operations
            allowed_tools=["Read", "Write", "Bash"],
            cwd=Path.cwd(),
            max_thinking_tokens=8000
        )
        
        responses = []
        
        try:
            async for message in query(prompt=full_prompt, options=options):
                self.message_history.append({
                    'type': message.__class__.__name__,
                    'timestamp': time.time()
                })
                
                # Extract text from different message types
                if hasattr(message, 'content') and message.__class__.__name__ == 'AssistantMessage':
                    for block in message.content:
                        if hasattr(block, 'text'):
                            responses.append(block.text)
                        elif hasattr(block, 'name') and block.name == 'Write':
                            # Handle file write operations
                            file_path = getattr(block.input, 'file_path', 'unknown')
                            responses.append(f"[Created file: {file_path}]")
                            
        except CLIJSONDecodeError as e:
            print(f"JSON parsing error for {self.agent_id}: {e}")
            # Try to parse as NDJSON
            responses = self._parse_ndjson_error(str(e))
            
        except CLINotFoundError:
            return "Error: Claude Code CLI not installed. Run: npm install -g @anthropic-ai/claude-code"
            
        except ProcessError as e:
            return f"Error: Process failed with exit code {e.exit_code}"
            
        except Exception as e:
            print(f"Unexpected error for {self.agent_id}: {type(e).__name__}: {e}")
            return f"Error: {str(e)}"
        
        # Save context
        response_text = '\n'.join(responses)
        if response_text and self.session_manager:
            self.session_manager.save_context(self.agent_id, prompt, response_text)
        
        return response_text
    
    def _parse_ndjson_error(self, error_text: str) -> List[str]:
        """Parse NDJSON from error text"""
        results = []
        for line in error_text.split('\n'):
            if '{' in line and '}' in line:
                try:
                    # Extract JSON part
                    json_start = line.find('{')
                    json_str = line[json_start:]
                    data = json.loads(json_str)
                    if isinstance(data, dict) and 'text' in data:
                        results.append(data['text'])
                except:
                    continue
        return results


async def test_basic_functionality():
    """Test basic functionality with improved error handling"""
    print("=== Test 1: Basic Functionality ===\n")
    
    agent = ImprovedClaudeAgent("basic-agent")
    
    response = await agent.ask("Write a simple Python function to reverse a string")
    
    success = 'def' in response and len(response) > 20
    print(f"Success: {success}")
    print(f"Response length: {len(response)} chars")
    if response:
        print(f"Preview: {response[:200]}...")
    
    return success


async def test_session_management():
    """Test custom session management"""
    print("\n=== Test 2: Session Management ===\n")
    
    session_mgr = SessionManager()
    agent = ImprovedClaudeAgent("session-agent", session_manager=session_mgr)
    
    # First interaction
    response1 = await agent.ask("My name is Bob and I'm working on a weather app.")
    print(f"Initial response: {response1[:100]}...")
    
    # Second interaction with context
    response2 = await agent.ask("What's my name and what am I working on?", include_context=True)
    print(f"\nWith context: {response2[:150]}...")
    
    remembers_name = 'Bob' in response2
    remembers_project = 'weather' in response2.lower()
    
    print(f"Remembers name: {remembers_name}")
    print(f"Remembers project: {remembers_project}")
    
    return remembers_name and remembers_project


async def test_concurrent_agents_safe():
    """Test concurrent agents with proper error handling"""
    print("\n=== Test 3: Safe Concurrent Execution ===\n")
    
    tasks = [
        ("agent-1", "Write a Python function to check if a number is even"),
        ("agent-2", "Write a Python function to calculate factorial"),
        ("agent-3", "Write a Python function to find the maximum in a list")
    ]
    
    async def safe_agent_task(agent_id: str, task: str):
        """Wrapped agent task with error handling"""
        agent = ImprovedClaudeAgent(agent_id)
        start_time = time.time()
        
        try:
            response = await agent.ask(task)
            duration = time.time() - start_time
            success = 'def' in response and len(response) > 20
            
            return {
                'agent_id': agent_id,
                'success': success,
                'duration': duration,
                'response_length': len(response),
                'error': None
            }
        except Exception as e:
            return {
                'agent_id': agent_id,
                'success': False,
                'duration': time.time() - start_time,
                'response_length': 0,
                'error': str(e)
            }
    
    # Run with proper task group error handling
    start_time = time.time()
    results = await asyncio.gather(*[
        safe_agent_task(agent_id, task) for agent_id, task in tasks
    ], return_exceptions=True)
    total_duration = time.time() - start_time
    
    # Filter out exceptions
    valid_results = [r for r in results if isinstance(r, dict)]
    successful = sum(1 for r in valid_results if r['success'])
    
    print(f"Total time: {total_duration:.2f}s")
    print(f"Successful: {successful}/{len(tasks)}")
    
    for result in valid_results:
        status = "✓" if result['success'] else "✗"
        print(f"  {result['agent_id']}: {status} ({result['duration']:.2f}s)")
        if result['error']:
            print(f"    Error: {result['error']}")
    
    return successful >= 2  # At least 2/3 success


async def test_specialized_agents():
    """Test agent specialization with system prompts"""
    print("\n=== Test 4: Agent Specialization ===\n")
    
    agents = {
        'optimizer': ImprovedClaudeAgent(
            "optimizer",
            "You are a code optimization expert. Always suggest performance improvements."
        ),
        'security': ImprovedClaudeAgent(
            "security",
            "You are a security expert. Always point out potential security issues."
        )
    }
    
    code_sample = """
def get_user_data(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)
"""
    
    results = {}
    
    for agent_type, agent in agents.items():
        response = await agent.ask(f"Review this code:\n{code_sample}")
        print(f"\n{agent_type.capitalize()} Agent Response:")
        print(response[:200] + "...")
        
        if agent_type == 'optimizer':
            results[agent_type] = 'performance' in response.lower() or 'optimize' in response.lower()
        elif agent_type == 'security':
            results[agent_type] = 'sql injection' in response.lower() or 'security' in response.lower()
    
    return all(results.values())


async def main():
    """Run all fixed tests"""
    print("Fixed Claude Code SDK Tests")
    print("=" * 50)
    print()
    
    # Check CLI installation first
    try:
        test_agent = ImprovedClaudeAgent("test")
        test_response = await test_agent.ask("Say 'test'")
        if "not installed" in test_response:
            print("ERROR: Claude Code CLI not installed")
            print("Run: npm install -g @anthropic-ai/claude-code")
            return False
    except Exception as e:
        print(f"Setup error: {e}")
        return False
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Session Management", test_session_management),
        ("Safe Concurrent Execution", test_concurrent_agents_safe),
        ("Agent Specialization", test_specialized_agents)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            passed = await test_func()
            results.append({'name': test_name, 'passed': passed})
        except Exception as e:
            print(f"\nERROR in {test_name}: {e}")
            results.append({'name': test_name, 'passed': False})
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    passed_count = sum(1 for r in results if r['passed'])
    
    for result in results:
        status = "✅ PASSED" if result['passed'] else "❌ FAILED"
        print(f"{result['name']}: {status}")
    
    print(f"\nTotal: {passed_count}/{len(results)} passed")
    
    # Save results
    with open('fixed_test_results.json', 'w') as f:
        json.dump({
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'results': results,
            'solutions_applied': [
                'Custom SessionManager for conversation persistence',
                'Safe error handling with try-except',
                'Permission mode set to acceptEdits',
                'NDJSON parsing for streaming responses',
                'Tool use block handling'
            ]
        }, f, indent=2)
    
    return passed_count == len(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)