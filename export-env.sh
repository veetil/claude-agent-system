#!/bin/bash

# Load .env file and export variables
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
done < .env

# Verify a few key variables (optional)
echo -e "\nVerification:"
echo "PYTHON_BACKEND_URL: $PYTHON_BACKEND_URL"
echo "TEMPLATE_NAME: $TEMPLATE_NAME"