#!/usr/bin/env python3
"""Quick test to verify the simple session management approach"""

import subprocess
import json
import time

def test_session_continuity():
    """Test that session IDs chain correctly"""
    
    print("Testing Claude CLI Session Continuity")
    print("=" * 40)
    
    # First call - establish context
    print("\n1. First interaction (establishing context)...")
    cmd1 = ['claude', '-p', 'My favorite color is blue and I have 3 cats.', '--output-format', 'json']
    result1 = subprocess.run(cmd1, capture_output=True, text=True)
    
    if result1.returncode != 0:
        print(f"Error: {result1.stderr}")
        return False
        
    response1 = json.loads(result1.stdout)
    session_id_1 = response1.get('session_id')
    print(f"Session ID: {session_id_1}")
    print(f"Response: {response1.get('message', '')[:100]}...")
    
    # Second call - use resume with session ID
    print("\n2. Second interaction (resuming session)...")
    cmd2 = ['claude', '-p', 'What is my favorite color?', '--output-format', 'json', '-r', session_id_1]
    result2 = subprocess.run(cmd2, capture_output=True, text=True)
    
    if result2.returncode != 0:
        print(f"Error: {result2.stderr}")
        return False
        
    response2 = json.loads(result2.stdout)
    session_id_2 = response2.get('session_id')
    print(f"New Session ID: {session_id_2}")
    print(f"Response: {response2.get('message', '')[:150]}...")
    
    # Check if context was maintained
    remembers_color = 'blue' in response2.get('message', '').lower()
    
    # Third call - continue chain
    print("\n3. Third interaction (continuing chain)...")
    cmd3 = ['claude', '-p', 'How many cats do I have?', '--output-format', 'json', '-r', session_id_2]
    result3 = subprocess.run(cmd3, capture_output=True, text=True)
    
    if result3.returncode != 0:
        print(f"Error: {result3.stderr}")
        return False
        
    response3 = json.loads(result3.stdout)
    session_id_3 = response3.get('session_id')
    print(f"New Session ID: {session_id_3}")
    print(f"Response: {response3.get('message', '')[:150]}...")
    
    # Check if context was maintained
    remembers_cats = '3' in response3.get('message', '') or 'three' in response3.get('message', '').lower()
    
    # Results
    print("\n" + "=" * 40)
    print("RESULTS:")
    print(f"✓ Session IDs update with each call: {session_id_1 != session_id_2 != session_id_3}")
    print(f"✓ Remembers color (blue): {remembers_color}")
    print(f"✓ Remembers cats (3): {remembers_cats}")
    print(f"✓ Session continuity works: {remembers_color and remembers_cats}")
    
    return remembers_color and remembers_cats

if __name__ == "__main__":
    success = test_session_continuity()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
    exit(0 if success else 1)