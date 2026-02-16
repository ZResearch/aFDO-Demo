#!/bin/bash
# Load .env and start Chat UI

if [ -f .env ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

python3 agents/chat_ui/chat_ui_agent.py
