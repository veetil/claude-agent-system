#!/usr/bin/env python3
"""Test session chaining with Claude CLI using -p and -r flags"""

import subprocess
import json

def run_claude(prompt, session_id=None):
    """Run Claude CLI with print mode and JSON output"""
    cmd = ['claude', '-p', prompt, '--output-format', 'json']
    
    if session_id:
        cmd.extend(['-r', session_id])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return None
    
    return json.loads(result.stdout)

def main():
    print("Testing Claude CLI Session Chaining")
    print("=" * 50)
    
    # First conversation
    print("\n1. First message - establishing favorite color")
    response1 = run_claude("My favorite color is blue")
    
    if response1:
        session_id_1 = response1.get('session_id')
        print(f"Session ID: {session_id_1}")
        print(f"Response: {response1.get('message', '')[:100]}...")
        
        # Second conversation - resume with session ID
        print(f"\n2. Second message - adding favorite car (resuming session {session_id_1})")
        response2 = run_claude("My favorite car is Honda", session_id_1)
        
        if response2:
            session_id_2 = response2.get('session_id')
            print(f"New Session ID: {session_id_2}")
            print(f"Response: {response2.get('message', '')[:100]}...")
            
            # Third conversation - check if it remembers both
            print(f"\n3. Third message - asking about both (resuming session {session_id_2})")
            response3 = run_claude("What are my favorite color and car?", session_id_2)
            
            if response3:
                session_id_3 = response3.get('session_id')
                print(f"New Session ID: {session_id_3}")
                print(f"Response: {response3.get('message', '')}")
                
                # Check if both were remembered
                message = response3.get('message', '').lower()
                remembers_color = 'blue' in message
                remembers_car = 'honda' in message
                
                print(f"\nRemembered color (blue): {remembers_color}")
                print(f"Remembered car (Honda): {remembers_car}")
                print(f"Session chain successful: {remembers_color and remembers_car}")

if __name__ == "__main__":
    main()