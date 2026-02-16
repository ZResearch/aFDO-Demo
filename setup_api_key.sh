#!/bin/bash

# Helper script to set up OpenAI API key

echo "=========================================="
echo "🔑 aFDO Demo - API Key Setup"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
fi

# Show current status
echo "Current .env file:"
echo "----------------------------------------"
cat .env
echo "----------------------------------------"
echo ""

# Prompt for API key
echo "Please enter your OpenAI API key:"
echo "(You can get one from https://platform.openai.com/api-keys)"
read -p "API Key: " api_key

# Validate it's not empty
if [ -z "$api_key" ]; then
    echo "❌ No API key entered. Exiting."
    exit 1
fi

# Update .env file
sed -i "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$api_key/" .env

echo ""
echo "✓ API key saved to .env file"
echo ""

# Verify
source .env
if [ "$OPENAI_API_KEY" = "your-openai-api-key-here" ]; then
    echo "❌ Error: API key not properly set"
    exit 1
fi

echo "✓ Configuration verified"
echo ""
echo "Next steps:"
echo "  1. Stop the system:  ./stop_system.sh"
echo "  2. Start the system: ./start_system.sh"
echo ""
echo "The system will now load the API key automatically!"
