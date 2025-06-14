#!/bin/bash

# Load .env.mcp file and export variables
while IFS= read -r line || [ -n "$line" ]; do
  # Skip comments and empty lines
  if [[ $line =~ ^[[:space:]]*$ || $line =~ ^[[:space:]]*# ]]; then
    continue
  fi
  
  # Remove leading/trailing whitespace
  line=$(echo "$line" | xargs)
  
  # Export the variable
  export "$line"
  
  # Extract variable name for display
  var_name=$(echo "$line" | cut -d= -f1)
  echo "Exported: $var_name"
done < .env.mcp

# Verify a few key MCP variables (optional)
echo -e "\nVerification:"
echo "GITHUB_TOKEN: ${GITHUB_TOKEN:0:20}..." 
echo "PERPLEXITY_API_KEY: ${PERPLEXITY_API_KEY:0:20}..."
echo "FIRECRAWL_API_KEY: ${FIRECRAWL_API_KEY:0:20}..."