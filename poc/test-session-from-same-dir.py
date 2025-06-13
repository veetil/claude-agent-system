#!/usr/bin/env python3
"""Test session continuity from the same directory"""

import subprocess
import json
import os

# Set working directory explicitly
work_dir = "/Users/mi/Projects/claude-sdk/poc"
os.chdir(work_dir)

print(f"Working directory: {os.getcwd()}")
print("=" * 50)

# First interaction
print("\n1. Creating initial session...")
result1 = subprocess.run(
    ['claude', '-p', 'Remember this: I have a red bicycle and 2 dogs.', '--output-format', 'json'],
    capture_output=True,
    text=True,
    cwd=work_dir
)

if result1.returncode == 0:
    resp1 = json.loads(result1.stdout)
    session_id = resp1.get('session_id')
    print(f"Session ID: {session_id}")
    print(f"Response: {resp1.get('message', '')[:100]}...")
    
    # Try to resume
    print(f"\n2. Resuming session {session_id}...")
    result2 = subprocess.run(
        ['claude', '-p', 'What color is my bicycle?', '--output-format', 'json', '-r', session_id],
        capture_output=True,
        text=True,
        cwd=work_dir
    )
    
    if result2.returncode == 0:
        resp2 = json.loads(result2.stdout)
        new_session_id = resp2.get('session_id')
        print(f"New Session ID: {new_session_id}")
        print(f"Response: {resp2.get('message', '')}")
        print(f"\nRemembered bicycle color: {'red' in resp2.get('message', '').lower()}")
    else:
        print(f"Error: {result2.stderr}")
        # Check if session file exists
        session_file = f"/Users/mi/.claude/projects/-Users-mi-Projects-claude-sdk-poc/{session_id}.jsonl"
        print(f"\nSession file exists: {os.path.exists(session_file)}")
        if os.path.exists(session_file):
            print("Session file found but Claude can't resume it.")
            print("This confirms print mode doesn't support session resumption.")
else:
    print(f"Error: {result1.stderr}")