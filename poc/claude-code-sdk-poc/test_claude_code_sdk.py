#!/usr/bin/env python3
"""
Test Claude Code SDK for multi-agent system capabilities
"""

import asyncio
import os
from typing import List, Dict, Any
from claude_code_sdk import query, ClaudeCodeOptions, ClaudeCodeMessage

class ClaudeCodeAgent:
    """Wrapper for Claude Code SDK agent with session management"""
    
    def __init__(self, agent_id: str, system_prompt: str = None, max_turns: int = 1):
        self.agent_id = agent_id
        self.system_prompt = system_prompt
        self.max_turns = max_turns
        self.conversation_history: List[ClaudeCodeMessage] = []
        
    async def ask(self, prompt: str) -> str:
        """Send a prompt and get response"""
        options = ClaudeCodeOptions(
            max_turns=self.max_turns,
            system_prompt=self.system_prompt
        )
        
        responses = []
        async for message in query(prompt=prompt, options=options):
            self.conversation_history.append(message)
            if message.type == "assistant":
                responses.append(message.content)
                
        return "\n".join(responses)
    
    async def continue_conversation(self, prompt: str, session_id: str = None) -> str:
        """Continue an existing conversation"""
        options = ClaudeCodeOptions(
            max_turns=self.max_turns,
            system_prompt=self.system_prompt,
            session_id=session_id  # Use session_id if supported
        )
        
        responses = []
        async for message in query(prompt=prompt, options=options):
            self.conversation_history.append(message)
            if message.type == "assistant":
                responses.append(message.content)
                
        return "\n".join(responses)


async def test_basic_interaction():
    """Test basic agent interaction"""
    print("=== Test 1: Basic Interaction ===\n")
    
    agent = ClaudeCodeAgent("agent-1")
    response = await agent.ask("Write a simple Python function that adds two numbers")
    
    print(f"Agent response:\n{response}\n")
    print(f"Contains function: {'def' in response}")
    print(f"Contains add operation: {'+' in response}")
    
    return 'def' in response


async def test_specialized_agents():
    """Test agents with different specializations via system prompts"""
    print("\n=== Test 2: Specialized Agents ===\n")
    
    # Create specialized agents
    code_reviewer = ClaudeCodeAgent(
        "reviewer",
        system_prompt="You are a code review specialist. Analyze code for best practices, potential bugs, and improvements."
    )
    
    test_writer = ClaudeCodeAgent(
        "test-writer",
        system_prompt="You are a test writing specialist. Write comprehensive unit tests for given code."
    )
    
    # Test code reviewer
    code_to_review = """
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)
"""
    
    review_response = await code_reviewer.ask(f"Review this code:\n{code_to_review}")
    print(f"Code Reviewer:\n{review_response}\n")
    
    # Test test writer
    test_response = await test_writer.ask(f"Write unit tests for this code:\n{code_to_review}")
    print(f"Test Writer:\n{test_response}\n")
    
    # Check specialization
    review_mentions_bug = "empty" in review_response.lower() or "zero" in review_response.lower()
    test_has_assert = "assert" in test_response.lower() or "test_" in test_response.lower()
    
    print(f"Reviewer identifies potential issue: {review_mentions_bug}")
    print(f"Test writer creates tests: {test_has_assert}")
    
    return review_mentions_bug and test_has_assert


async def test_concurrent_agents():
    """Test multiple agents running concurrently"""
    print("\n=== Test 3: Concurrent Agents ===\n")
    
    # Create multiple agents with different tasks
    agents_tasks = [
        ("agent-1", "Write a Python function to reverse a string"),
        ("agent-2", "Write a Python function to check if a number is prime"),
        ("agent-3", "Write a Python function to find factorial of a number"),
        ("agent-4", "Write a Python function to check palindrome"),
        ("agent-5", "Write a Python function to generate Fibonacci sequence")
    ]
    
    async def run_agent(agent_id: str, task: str):
        agent = ClaudeCodeAgent(agent_id)
        start_time = asyncio.get_event_loop().time()
        response = await agent.ask(task)
        end_time = asyncio.get_event_loop().time()
        return {
            "agent_id": agent_id,
            "task": task,
            "response": response,
            "duration": end_time - start_time,
            "success": "def" in response
        }
    
    # Run all agents concurrently
    start_time = asyncio.get_event_loop().time()
    results = await asyncio.gather(*[
        run_agent(agent_id, task) for agent_id, task in agents_tasks
    ])
    total_time = asyncio.get_event_loop().time() - start_time
    
    # Analyze results
    successful_agents = sum(1 for r in results if r["success"])
    avg_duration = sum(r["duration"] for r in results) / len(results)
    
    print(f"Total concurrent execution time: {total_time:.2f}s")
    print(f"Average individual agent time: {avg_duration:.2f}s")
    print(f"Successful agents: {successful_agents}/{len(agents_tasks)}")
    print(f"Speedup factor: {(avg_duration * len(results)) / total_time:.2f}x\n")
    
    for result in results:
        print(f"{result['agent_id']}: {'✓' if result['success'] else '✗'} ({result['duration']:.2f}s)")
    
    return successful_agents == len(agents_tasks)


async def test_session_continuation():
    """Test conversation continuation capabilities"""
    print("\n=== Test 4: Session Continuation ===\n")
    
    agent = ClaudeCodeAgent("session-agent", max_turns=3)
    
    # First interaction
    response1 = await agent.ask("My project is called 'DataAnalyzer' and it processes CSV files. Remember this.")
    print(f"Initial response: {response1}\n")
    
    # Try to continue conversation
    response2 = await agent.ask("What is my project called?")
    print(f"Continuation response: {response2}\n")
    
    # Check if context is maintained
    remembers_project = "DataAnalyzer" in response2
    print(f"Remembers project name: {remembers_project}")
    
    return remembers_project


async def test_multi_turn_conversation():
    """Test multi-turn conversation capabilities"""
    print("\n=== Test 5: Multi-turn Conversation ===\n")
    
    agent = ClaudeCodeAgent("multi-turn-agent", max_turns=5)
    
    # Complex multi-turn task
    response = await agent.ask("""
    I need to create a simple web server in Python. 
    First, show me the basic structure.
    Then add route handling.
    Finally, add error handling.
    """)
    
    print(f"Multi-turn response:\n{response}\n")
    
    # Check if response covers all aspects
    has_imports = "import" in response
    has_routes = "route" in response.lower() or "@app" in response
    has_error_handling = "except" in response or "error" in response.lower()
    
    print(f"Has imports: {has_imports}")
    print(f"Has routes: {has_routes}")
    print(f"Has error handling: {has_error_handling}")
    
    return has_imports and has_routes and has_error_handling


async def main():
    """Run all tests"""
    print("Claude Code SDK Testing")
    print("=" * 50)
    
    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        return
    
    tests = [
        ("Basic Interaction", test_basic_interaction),
        ("Specialized Agents", test_specialized_agents),
        ("Concurrent Agents", test_concurrent_agents),
        ("Session Continuation", test_session_continuation),
        ("Multi-turn Conversation", test_multi_turn_conversation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = await test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\nERROR in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    print(f"\nTotal: {passed_count}/{total_count} passed")
    
    # Save results
    import json
    with open("claude_code_sdk_test_results.json", "w") as f:
        json.dump({
            "tests": [{"name": name, "passed": passed} for name, passed in results],
            "summary": {
                "total": total_count,
                "passed": passed_count,
                "failed": total_count - passed_count
            }
        }, f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())