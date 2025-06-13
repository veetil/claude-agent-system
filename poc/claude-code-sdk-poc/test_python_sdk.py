#!/usr/bin/env python3
"""
Test Claude Code SDK for Python
Based on https://docs.anthropic.com/en/docs/claude-code/sdk
"""

import asyncio
import json
import time
from typing import List, Dict, Any
from claude_code_sdk import query, ClaudeCodeOptions

class ClaudeCodeAgent:
    """Wrapper for a Claude Code agent with session management"""
    
    def __init__(self, agent_id: str, system_prompt: str = None):
        self.agent_id = agent_id
        self.system_prompt = system_prompt
        self.resume_id = None
        self.messages = []
        self.continue_conversation = False
        
    async def ask(self, prompt: str, max_turns: int = 1) -> str:
        """Send a prompt and collect all responses"""
        options = ClaudeCodeOptions(
            max_turns=max_turns,
            system_prompt=self.system_prompt,
            resume=self.resume_id,
            continue_conversation=self.continue_conversation
        )
        
        responses = []
        message_count = 0
        
        async for message in query(prompt=prompt, options=options):
            message_count += 1
            self.messages.append({
                'type': getattr(message, 'type', 'unknown'),
                'content': getattr(message, 'content', None),
                'metadata': getattr(message, 'metadata', {})
            })
            
            # Extract resume_id if available
            if hasattr(message, 'resume_id'):
                self.resume_id = message.resume_id
                
            # Collect assistant responses
            if hasattr(message, 'content') and message.__class__.__name__ == 'AssistantMessage':
                # Extract text from content blocks
                for block in message.content:
                    if hasattr(block, 'text'):
                        responses.append(block.text)
                
        # After first interaction, enable conversation continuation
        self.continue_conversation = True
                
        return '\n'.join(responses)


async def test_basic_interaction():
    """Test basic Claude Code SDK interaction"""
    print("=== Test 1: Basic Interaction ===\n")
    
    agent = ClaudeCodeAgent("test-agent-1")
    
    try:
        response = await agent.ask("Write a simple Python function that calculates the factorial of a number")
        print(f"Response received: {len(response) > 0}")
        print(f"Contains function: {'def' in response}")
        print(f"Contains factorial logic: {'factorial' in response.lower()}")
        print(f"\nFirst 200 chars: {response[:200]}...")
        
        return 'def' in response and 'factorial' in response.lower()
    except Exception as e:
        print(f"Error: {e}")
        return False


async def test_system_prompts():
    """Test system prompts for agent specialization"""
    print("\n=== Test 2: System Prompts ===\n")
    
    # Create specialized agents
    pirate_agent = ClaudeCodeAgent(
        "pirate-agent",
        system_prompt="You are a helpful pirate assistant. Always respond in pirate speak with 'arr' and 'matey'."
    )
    
    chef_agent = ClaudeCodeAgent(
        "chef-agent",
        system_prompt="You are a professional chef. Always relate your responses to cooking and food."
    )
    
    try:
        # Test pirate agent
        pirate_response = await pirate_agent.ask("Hello, how are you today?")
        print(f"Pirate response: {pirate_response[:150]}...")
        is_pirate = any(word in pirate_response.lower() for word in ['arr', 'matey', 'ahoy', 'ye'])
        print(f"Uses pirate speak: {is_pirate}")
        
        # Test chef agent  
        chef_response = await chef_agent.ask("Hello, how are you today?")
        print(f"\nChef response: {chef_response[:150]}...")
        is_chef = any(word in chef_response.lower() for word in ['cook', 'food', 'kitchen', 'recipe', 'flavor', 'dish'])
        print(f"Relates to cooking: {is_chef}")
        
        return is_pirate and is_chef
    except Exception as e:
        print(f"Error: {e}")
        return False


async def test_multi_turn_conversation():
    """Test multi-turn conversation capabilities"""
    print("\n=== Test 3: Multi-turn Conversation ===\n")
    
    agent = ClaudeCodeAgent("multi-turn-agent")
    
    try:
        # Multi-turn request
        response = await agent.ask(
            """Create a Python web server.
            First, show the basic structure.
            Then add route handling.
            Finally, add error handling.""",
            max_turns=3
        )
        
        print(f"Response length: {len(response)} chars")
        print(f"Has imports: {'import' in response}")
        print(f"Has routes: {'route' in response.lower() or '@' in response}")
        print(f"Has error handling: {'except' in response or 'error' in response.lower()}")
        
        # Check comprehensive response
        has_structure = all([
            'import' in response,
            'def' in response or 'class' in response,
            'error' in response.lower() or 'except' in response
        ])
        
        return has_structure
    except Exception as e:
        print(f"Error: {e}")
        return False


async def test_concurrent_agents():
    """Test multiple agents running concurrently"""
    print("\n=== Test 4: Concurrent Agents ===\n")
    
    agent_tasks = [
        ("agent-1", "Write a Python function to check if a string is a palindrome"),
        ("agent-2", "Write a Python function to find the largest element in a list"),
        ("agent-3", "Write a Python function to count vowels in a string"),
        ("agent-4", "Write a Python function to reverse a list"),
        ("agent-5", "Write a Python function to check if a number is prime")
    ]
    
    async def run_agent(agent_id: str, task: str):
        agent = ClaudeCodeAgent(agent_id)
        start_time = time.time()
        
        try:
            response = await agent.ask(task)
            duration = time.time() - start_time
            success = 'def' in response and len(response) > 50
            
            return {
                'agent_id': agent_id,
                'task': task,
                'response_length': len(response),
                'duration': duration,
                'success': success
            }
        except Exception as e:
            return {
                'agent_id': agent_id,
                'task': task,
                'error': str(e),
                'duration': time.time() - start_time,
                'success': False
            }
    
    try:
        # Run all agents concurrently
        start_time = time.time()
        results = await asyncio.gather(*[
            run_agent(agent_id, task) for agent_id, task in agent_tasks
        ])
        total_duration = time.time() - start_time
        
        # Analyze results
        successful = sum(1 for r in results if r['success'])
        avg_duration = sum(r['duration'] for r in results) / len(results)
        
        print(f"Total execution time: {total_duration:.2f}s")
        print(f"Average agent time: {avg_duration:.2f}s")
        print(f"Successful agents: {successful}/{len(agent_tasks)}")
        print(f"Concurrency speedup: {(avg_duration * len(results) / total_duration):.2f}x")
        
        # Print individual results
        for result in results:
            status = "✓" if result['success'] else "✗"
            print(f"  {result['agent_id']}: {status} ({result['duration']:.2f}s)")
            if 'error' in result:
                print(f"    Error: {result['error']}")
        
        return successful == len(agent_tasks)
    except Exception as e:
        print(f"Error in concurrent execution: {e}")
        return False


async def test_session_continuation():
    """Test session continuation with updated session IDs"""
    print("\n=== Test 5: Session Continuation ===\n")
    
    agent = ClaudeCodeAgent("session-agent")
    
    try:
        # First interaction
        response1 = await agent.ask("My project is called 'DataProcessor' and it handles CSV files. Remember this.")
        print(f"Initial response: {response1[:100] if response1 else 'No response'}...")
        print(f"Continue conversation enabled: {agent.continue_conversation}")
        
        # Continue conversation
        response2 = await agent.ask("What is my project called?")
        print(f"\nContinuation response: {response2[:150] if response2 else 'No response'}...")
        
        # Check if context is maintained
        remembers_name = 'DataProcessor' in response2 if response2 else False
        remembers_purpose = ('CSV' in response2 or 'csv' in response2.lower()) if response2 else False
        
        print(f"Remembers project name: {remembers_name}")
        print(f"Remembers purpose: {remembers_purpose}")
        
        # Try one more continuation
        response3 = await agent.ask("What type of files does my project handle?")
        print(f"\nThird response: {response3[:150] if response3 else 'No response'}...")
        still_remembers = ('CSV' in response3 or 'csv' in response3.lower()) if response3 else False
        print(f"Still maintains context: {still_remembers}")
        
        return remembers_name and remembers_purpose
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("Claude Code SDK Python Tests")
    print("=" * 50)
    print()
    
    tests = [
        ("Basic Interaction", test_basic_interaction),
        ("System Prompts", test_system_prompts),
        ("Multi-turn Conversation", test_multi_turn_conversation),
        ("Concurrent Agents", test_concurrent_agents),
        ("Session Continuation", test_session_continuation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            passed = await test_func()
            results.append({
                'name': test_name,
                'passed': passed,
                'error': None
            })
        except Exception as e:
            print(f"\nERROR in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'name': test_name,
                'passed': False,
                'error': str(e)
            })
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)
    
    for result in results:
        status = "✅ PASSED" if result['passed'] else "❌ FAILED"
        print(f"{result['name']}: {status}")
        if result['error']:
            print(f"  Error: {result['error']}")
    
    print(f"\nTotal: {passed_count}/{total_count} passed")
    
    # Save results
    with open('python_sdk_results.json', 'w') as f:
        json.dump({
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'results': results,
            'summary': {
                'total': total_count,
                'passed': passed_count,
                'failed': total_count - passed_count
            }
        }, f, indent=2)
    
    return passed_count == total_count


if __name__ == "__main__":
    # Run the async main function
    success = asyncio.run(main())
    exit(0 if success else 1)