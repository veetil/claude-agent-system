#!/usr/bin/env python3
"""Test session chaining with Claude CLI using -p and -r flags,
   print the directory, and add a 5-second delay between calls."""

import subprocess
import json
import sys
import os
import time

def run_claude(prompt, session_id=None):
    """Run Claude CLI with print mode and JSON output, showing current directory."""
    cwd = os.getcwd()
    print(f"[run_claude] Running in directory: {cwd}")

    cmd = ['claude', '-p', prompt, '--output-format', 'json']
    if session_id:
        cmd.extend(['-r', session_id])
    print("running cmd",cmd)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        return None

    stdout = result.stdout
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        # attempt to extract JSON block
        json_start = stdout.find('{')
        if json_start == -1:
            print("Failed to parse JSON from Claude CLI output.", file=sys.stderr)
            return None
        try:
            data = json.loads(stdout[json_start:])
        except json.JSONDecodeError:
            print("Failed to parse JSON from Claude CLI output.", file=sys.stderr)
            return None

    return data

def main():
    print("Testing Claude CLI Session Chaining")
    print("=" * 50)

    # 1. First conversation
    print("\n1. First message - establishing favorite color")
    response1 = run_claude("My favorite color is blue")
    if not response1:
        return
    time.sleep(5)

    session_id_1 = response1.get('session_id')
    print(f"Session ID: {session_id_1}")
    print(f"Response: {response1.get('result', '')[:100]}...")

    # 2. Second conversation - resume with session ID
    print(f"\n2. Second message - adding favorite car (resuming session {session_id_1})")
    response2 = run_claude("My favorite car is Honda", session_id_1)
    if not response2:
        return
    time.sleep(5)

    session_id_2 = response2.get('session_id')
    print(f"New Session ID: {session_id_2}")
    print(f"Response: {response2.get('result', '')[:100]}...")

    # 3. Third conversation - check if it remembers both
    print(f"\n3. Third message - asking about both (resuming session {session_id_2})")
    response3 = run_claude("What are my favorite color and car?", session_id_2)
    if not response3:
        return
    time.sleep(5)

    session_id_3 = response3.get('session_id')
    reply = response3.get('result', '')
    print(f"New Session ID: {session_id_3}")
    print(f"Response: {reply}")

    # Validate remembering
    remembers_color = 'blue' in reply.lower()
    remembers_car   = 'honda' in reply.lower()
    print(f"\nRemembered color (blue): {remembers_color}")
    print(f"Remembered car (Honda): {remembers_car}")
    print(f"Session chain successful: {remembers_color and remembers_car}")

if __name__ == "__main__":
    main()
