#!/usr/bin/env python3
"""Basic Claude Code SDK test to verify functionality"""

import asyncio
from claude_code_sdk import query, ClaudeCodeOptions

async def test_basic():
    """Test basic functionality"""
    print("Testing Claude Code SDK...\n")
    
    # Test 1: Simple query
    print("1. Simple query test:")
    responses = []
    
    try:
        async for message in query(
            prompt="Write a Python function that adds two numbers",
            options=ClaudeCodeOptions(max_turns=1)
        ):
            if hasattr(message, 'content') and message.__class__.__name__ == 'AssistantMessage':
                for block in message.content:
                    if hasattr(block, 'text'):
                        responses.append(block.text)
        
        full_response = '\n'.join(responses)
        print(f"Got response: {'def' in full_response}")
        print(f"Response length: {len(full_response)} chars")
        print(f"First 200 chars: {full_response[:200]}...")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
    # Test 2: System prompt
    print("\n2. System prompt test:")
    pirate_responses = []
    
    try:
        async for message in query(
            prompt="Hello, how are you?",
            options=ClaudeCodeOptions(
                system_prompt="You are a pirate. Always speak like a pirate with 'arr' and 'matey'.",
                max_turns=1
            )
        ):
            if hasattr(message, 'content') and message.__class__.__name__ == 'AssistantMessage':
                for block in message.content:
                    if hasattr(block, 'text'):
                        pirate_responses.append(block.text)
        
        pirate_text = '\n'.join(pirate_responses)
        print(f"Got pirate response: {len(pirate_text) > 0}")
        print(f"Uses pirate speak: {any(word in pirate_text.lower() for word in ['arr', 'matey', 'ahoy'])}")
        print(f"Response: {pirate_text[:150]}...")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_basic())