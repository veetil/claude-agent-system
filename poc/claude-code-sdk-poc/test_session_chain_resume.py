#!/usr/bin/env python3
"""Run a single Claude CLI query (adding favorite car) given an existing session ID."""

import subprocess
import json
import sys
import os

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <session_id>", file=sys.stderr)
        sys.exit(1)
    session_id = sys.argv[1]

    cwd = os.getcwd()
    print(f"[run_claude] Running in directory: {cwd}")

    cmd = [
        "claude",
        "-p", "My favorite car is Honda",
        "--output-format", "json",
        "-r", session_id
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"Error running claude: {proc.stderr}", file=sys.stderr)
        sys.exit(proc.returncode)

    out = proc.stdout
    # strip any logs before the JSON
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        idx = out.find("{")
        if idx == -1:
            print("Could not find JSON output.", file=sys.stderr)
            sys.exit(1)
        data = json.loads(out[idx:])

    new_session = data.get("session_id")
    reply      = data.get("result")

    print(f"New session_id: {new_session}")
    print(f"Reply: {reply}")

if __name__ == "__main__":
    main()
