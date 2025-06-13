#!/usr/bin/env python3
"""
Test session management using Claude Python SDK
"""

import os
import json
from anthropic import Anthropic
from typing import List, Dict, Any

# Initialize the client
client = Anthropic(
    # api_key will be read from ANTHROPIC_API_KEY env var
)

class ConversationSession:
    """Manages a conversation session with Claude"""
    
    def __init__(self, system_prompt: str = None):
        self.messages: List[Dict[str, str]] = []
        self.system_prompt = system_prompt
        
    def add_user_message(self, content: str):
        """Add a user message to the conversation"""
        self.messages.append({
            "role": "user",
            "content": content
        })
        
    def add_assistant_message(self, content: str):
        """Add an assistant message to the conversation"""
        self.messages.append({
            "role": "assistant", 
            "content": content
        })
        
    def get_response(self, user_message: str) -> str:
        """Get a response from Claude while maintaining conversation history"""
        self.add_user_message(user_message)
        
        # Create the API call
        kwargs = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 1024,
            "messages": self.messages
        }
        
        if self.system_prompt:
            kwargs["system"] = self.system_prompt
            
        response = client.messages.create(**kwargs)
        
        # Extract the response text
        response_text = response.content[0].text
        
        # Add to conversation history
        self.add_assistant_message(response_text)
        
        return response_text


def test_basic_session():
    """Test basic session management"""
    print("=== Test 1: Basic Session Management ===\n")
    
    # Create a session
    session = ConversationSession()
    
    # First message
    response1 = session.get_response("My name is Alice and my favorite color is blue.")
    print(f"Response 1: {response1}")
    
    # Second message - should remember context
    response2 = session.get_response("What is my name?")
    print(f"\nResponse 2: {response2}")
    print(f"Remembers name: {'Alice' in response2}")
    
    # Third message - should remember both facts
    response3 = session.get_response("What is my favorite color?")
    print(f"\nResponse 3: {response3}")
    print(f"Remembers color: {'blue' in response3}")
    
    return 'Alice' in response2 and 'blue' in response3


def test_multiple_sessions():
    """Test isolation between multiple sessions"""
    print("\n=== Test 2: Multiple Session Isolation ===\n")
    
    # Create two separate sessions
    session1 = ConversationSession()
    session2 = ConversationSession()
    
    # Set up different context in each session
    response1_1 = session1.get_response("My name is Bob and I like pizza.")
    print(f"Session 1 setup: {response1_1}")
    
    response2_1 = session2.get_response("My name is Carol and I like sushi.")
    print(f"Session 2 setup: {response2_1}")
    
    # Test isolation
    response1_2 = session1.get_response("What is my name and what do I like?")
    print(f"\nSession 1 query: {response1_2}")
    print(f"Session 1 correct: {'Bob' in response1_2 and 'pizza' in response1_2}")
    
    response2_2 = session2.get_response("What is my name and what do I like?")
    print(f"\nSession 2 query: {response2_2}")
    print(f"Session 2 correct: {'Carol' in response2_2 and 'sushi' in response2_2}")
    
    # Check for cross-contamination
    no_contamination = ('Carol' not in response1_2 and 'Bob' not in response2_2)
    print(f"\nNo cross-contamination: {no_contamination}")
    
    return no_contamination


def test_system_prompts():
    """Test different system prompts for agent specialization"""
    print("\n=== Test 3: System Prompts for Agent Specialization ===\n")
    
    # Create specialized agents
    pirate_agent = ConversationSession(
        system_prompt="You are a helpful pirate. Always respond in pirate speak with 'arr' and 'matey'."
    )
    
    chef_agent = ConversationSession(
        system_prompt="You are a professional chef. Always relate your responses to cooking and food."
    )
    
    # Test pirate agent
    pirate_response = pirate_agent.get_response("Hello, how are you?")
    print(f"Pirate agent: {pirate_response}")
    is_pirate = 'arr' in pirate_response.lower() or 'matey' in pirate_response.lower()
    print(f"Uses pirate speak: {is_pirate}")
    
    # Test chef agent
    chef_response = chef_agent.get_response("Hello, how are you?")
    print(f"\nChef agent: {chef_response}")
    is_chef = any(word in chef_response.lower() for word in ['cook', 'food', 'kitchen', 'recipe', 'dish', 'meal'])
    print(f"Relates to cooking: {is_chef}")
    
    return is_pirate and is_chef


def test_conversation_continuity():
    """Test maintaining context over multiple turns"""
    print("\n=== Test 4: Conversation Continuity ===\n")
    
    session = ConversationSession()
    
    # Build up context over multiple turns
    facts = []
    
    response1 = session.get_response("I'm planning a trip to Paris.")
    print(f"Turn 1: {response1}")
    facts.append("Paris")
    
    response2 = session.get_response("I'll be there for 5 days.")
    print(f"\nTurn 2: {response2}")
    facts.append("5 days")
    
    response3 = session.get_response("I'm especially interested in art museums.")
    print(f"\nTurn 3: {response3}")
    facts.append("art museums")
    
    # Test if all context is maintained
    response4 = session.get_response("Can you summarize my travel plans?")
    print(f"\nSummary request: {response4}")
    
    # Check if all facts are remembered
    all_facts_remembered = all(fact.lower() in response4.lower() for fact in facts)
    print(f"\nAll facts remembered: {all_facts_remembered}")
    
    return all_facts_remembered


def main():
    """Run all tests"""
    print("Claude Python SDK Session Management Tests")
    print("=" * 50)
    
    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        return
    
    tests = [
        ("Basic Session", test_basic_session),
        ("Multiple Sessions", test_multiple_sessions),
        ("System Prompts", test_system_prompts),
        ("Conversation Continuity", test_conversation_continuity)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\nERROR in {test_name}: {e}")
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


if __name__ == "__main__":
    main()