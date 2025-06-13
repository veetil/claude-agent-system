#!/usr/bin/env python3
"""Simple test to understand Claude Code SDK message types"""

import asyncio
from claude_code_sdk import query, ClaudeCodeOptions

async def simple_test():
    print("=== Simple Claude Code SDK Test ===\n")
    
    # Test 1: Basic query
    print("Test 1: Basic query")
    message_count = 0
    
    async for message in query(
        prompt="Say hello and write a simple add function",
        options=ClaudeCodeOptions(max_turns=1)
    ):
        message_count += 1
        print(f"\nMessage {message_count}:")
        print(f"  Type: {type(message).__name__}")
        print(f"  Attributes: {dir(message)}")
        
        if hasattr(message, 'type'):
            print(f"  Message type: {message.type}")
        if hasattr(message, 'content'):
            print(f"  Content preview: {message.content[:100]}...")
        if hasattr(message, 'text'):
            print(f"  Text preview: {message.text[:100]}...")
            
    # Test 2: With system prompt
    print("\n\nTest 2: With system prompt")
    message_count = 0
    
    async for message in query(
        prompt="Hello",
        options=ClaudeCodeOptions(
            system_prompt="You are a pirate. Always respond in pirate speak.",
            max_turns=1
        )
    ):
        message_count += 1
        print(f"\nMessage {message_count}:")
        print(f"  Type: {type(message).__name__}")
        
        # Try to extract content
        content = None
        if hasattr(message, 'content'):
            content = message.content
        elif hasattr(message, 'text'):
            content = message.text
        elif hasattr(message, 'result'):
            content = message.result
            
        if content:
            print(f"  Content: {content[:150]}...")

if __name__ == "__main__":
    asyncio.run(simple_test())