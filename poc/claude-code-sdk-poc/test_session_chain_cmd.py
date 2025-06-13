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
def call_claude(prompt, resume_id=None):
    """Invoke Claude CLI in JSON mode; place -r before -p to ensure resume."""
    cmd = ["claude"]
    if resume_id:
        cmd += ["-r", resume_id]  # resume flag first :contentReference[oaicite:8]{index=8}
    cmd += ["-p", prompt, "--output-format", "json"]

    # ←–– Add this:
    print("Running command:\n  " + shlex.join(cmd))
    # Optionally add --verbose for debugging:
    # cmd.append("--verbose")

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"[Error] {proc.stderr.strip()}", file=sys.stderr)
        sys.exit(proc.returncode)

    # Strip logs before JSON
    out = proc.stdout.strip()
    idx = out.find("{")
    out = out[idx:] if idx > 0 else out
    return json.loads(out)

def main():
    # 1) First query
    resp1 = call_claude("my fav color is magenta")
    print(resp1)
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
