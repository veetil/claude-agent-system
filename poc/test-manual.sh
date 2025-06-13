#!/bin/bash

echo "=== Manual Session Test ==="
echo

echo "Step 1: Create session"
RESPONSE1=$(echo "My name is Bob" | claude --print --output-format json)
echo "$RESPONSE1" | jq .
SESSION1=$(echo "$RESPONSE1" | jq -r .session_id)
echo "Session ID: $SESSION1"
echo

echo "Step 2: Continue with -r $SESSION1"
RESPONSE2=$(echo "What is my name?" | claude --print --output-format json -r "$SESSION1")
echo "$RESPONSE2" | jq .
SESSION2=$(echo "$RESPONSE2" | jq -r .session_id)
echo "New Session ID: $SESSION2"
echo

echo "Step 3: Continue with updated session ID $SESSION2"
RESPONSE3=$(echo "Tell me my name again" | claude --print --output-format json -r "$SESSION2")
echo "$RESPONSE3" | jq .