#!/usr/bin/env python3
"""
three_chat_json_fixed.py

Run three sequential Claude CLI queries in JSON mode, chaining session IDs:
1. “what is my fav color”
2. “My favorite car is Honda” (resuming session from step 1)
3. “What are my favorite color and car?” (resuming session from step 2)
"""

import subprocess
import json
import sys
import shlex
import os

# detect your login shell (e.g. /bin/zsh or /bin/bash)
SHELL = os.environ.get("SHELL", "/bin/bash")

def call_claude(prompt, resume_id=None):
    """Invoke Claude CLI in JSON mode via your interactive login shell."""
    # build the claude command
    args = ["claude"]
    if resume_id:
        args += ["-r", resume_id]
    args += ["-p", prompt, "--output-format", "json"]

    # quote it for the shell
    shell_cmd = " ".join(shlex.quote(a) for a in args)
    print(f"Running command with {SHELL} -ic:\n  {shell_cmd}")

    # run under your interactive shell so aliases in ~/.zshrc (or ~/.bashrc) load
    proc = subprocess.run(
        [SHELL, "-ic", shell_cmd],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(f"[Error] {proc.stderr.strip()}", file=sys.stderr)
        sys.exit(proc.returncode)

    # strip any prepended logs so we start at the JSON object
    out = proc.stdout.strip()
    idx = out.find("{")
    out = out[idx:] if idx > 0 else out
    return json.loads(out)

def main():
    # 1) First query
    resp1 = call_claude("my fav color is magenta")
    sid1 = resp1["session_id"]
    print(f"Session 1 ID: {sid1}")
    print(f"Response 1: {resp1['result']}\n")

    # 2) Second query, resuming session 1
    resp2 = call_claude("My favorite car is Honda", resume_id=sid1)
    sid2 = resp2["session_id"]
    print(f"Session 2 ID: {sid2}")
    print(f"Response 2: {resp2['result']}\n")

    # 3) Third query, resuming session 2
    resp3 = call_claude("What are my favorite color and car?", resume_id=sid2)
    sid3 = resp3["session_id"]
    print(f"Session 3 ID: {sid3}")
    print(f"Response 3: {resp3['result']}\n")

if __name__ == "__main__":
    main()
