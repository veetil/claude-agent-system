#!/bin/bash
# Run fixed SDK tests with proper environment

echo "Setting up environment for Claude Code SDK tests..."

# Ensure claude-code is accessible
export CLAUDE_CODE_PATH="/opt/homebrew/lib/node_modules/@anthropic-ai/claude-code/cli.js"

# Create a temporary wrapper
cat > /tmp/claude-code << 'EOF'
#!/bin/bash
exec node "/opt/homebrew/lib/node_modules/@anthropic-ai/claude-code/cli.js" "$@"
EOF

chmod +x /tmp/claude-code
export PATH="/tmp:$PATH"

# Verify claude-code is available
echo "Checking claude-code availability..."
claude-code --version

# Set ANTHROPIC_API_KEY if not already set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "Warning: ANTHROPIC_API_KEY not set"
fi

# Run the tests
echo "Running fixed SDK tests..."
python fixed_claude_sdk_tests.py

# Cleanup
rm -f /tmp/claude-code