#!/bin/bash
# Setup environment for aFDO Demo

# TODO: Replace with your actual OpenAI API key
export OPENAI_API_KEY='PUT_YOUR_API_KEY_HERE'

# Verify
if [ "$OPENAI_API_KEY" = "PUT_YOUR_API_KEY_HERE" ]; then
    echo "⚠️  ERROR: Please edit setup_env.sh and add your actual API key"
    exit 1
fi

echo "✓ Environment configured"
echo "  OPENAI_API_KEY: ${OPENAI_API_KEY:0:10}... (${#OPENAI_API_KEY} chars)"
