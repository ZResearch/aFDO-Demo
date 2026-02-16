#!/bin/bash

# start_system.sh - Start all aFDO agents for IJCAI 2026 demo
# Improved version with better error handling

# Don't exit on first error - try to start all agents
# set -e  # REMOVED - we want to try starting all agents

# Load environment variables from .env file
if [ -f .env ]; then
    echo "📄 Loading environment from .env file..."
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
    echo "✓ Environment loaded"
else
    echo "⚠️  No .env file found. Create one from .env.example"
fi

echo "=========================================="
echo "🚀 Starting aFDO Demo System"
echo "=========================================="
echo ""

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set"
    echo "   LLM-powered agents will not work"
    echo ""
fi

# Create logs directory
mkdir -p logs

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to start an agent
start_agent() {
    local name=$1
    local script=$2
    local port=$3

    echo "Starting $name (port $port)..."

    # Check if port is already in use
    if check_port $port; then
        echo "  ⚠️  Port $port already in use - skipping"
        # Try to save PID if we can find it
        local existing_pid=$(lsof -ti :$port 2>/dev/null | head -1)
        if [ -n "$existing_pid" ]; then
            echo $existing_pid > logs/$name.pid
            echo "  ℹ️  Saved existing PID: $existing_pid"
        fi
        return 1
    fi

    # Make sure we're in the right directory
    cd /home/boukhers/IJCAI_DEMO

    # Start the agent with explicit environment
    nohup env \
        OPENAI_API_KEY="$OPENAI_API_KEY" \
        OPENAI_API_BASE="$OPENAI_API_BASE" \
        LLM_MODEL="$LLM_MODEL" \
        python3 $script > logs/$name.log 2>&1 &

    local pid=$!
    echo $pid > logs/$name.pid

    # Give it a moment to start
    sleep 3

    # Verify it's running
    if ps -p $pid > /dev/null 2>&1; then
        # Check if it successfully bound to the port
        sleep 2
        if check_port $port; then
            echo "  ✅ Started (PID $pid)"
            return 0
        else
            echo "  ⚠️  Process started but port $port not listening yet"
            echo "     Check logs/$name.log for errors"
            return 0
        fi
    else
        echo "  ❌ Failed to start! Check logs/$name.log"
        tail -20 logs/$name.log
        rm -f logs/$name.pid
        return 1
    fi
}

# Track failures
FAILED=0
STARTED=0

# Start agents in order
echo "1. Starting FDO Registry..."
if start_agent "registry" "registry/main.py" "8000"; then
    STARTED=$((STARTED+1))
else
    FAILED=$((FAILED+1))
fi

echo ""
echo "2. Starting infrastructure agents..."
if start_agent "creator" "agents/creator/creator_agent.py" "8006"; then
    STARTED=$((STARTED+1))
else
    FAILED=$((FAILED+1))
fi

echo ""
echo "3. Starting LLM endpoints..."
if start_agent "llm-gpt4" "agents/llm_endpoint_gpt4/llm_endpoint_agent.py" "8007"; then
    STARTED=$((STARTED+1))
else
    FAILED=$((FAILED+1))
fi
if start_agent "llm-gpt4-mini" "agents/llm_endpoint_gpt4_mini/llm_endpoint_agent.py" "8008"; then
    STARTED=$((STARTED+1))
else
    FAILED=$((FAILED+1))
fi

echo ""
echo "4. Starting task agents..."
if start_agent "pdf-parser" "agents/pdf_parser/pdf_parser_agent.py" "8004"; then
    STARTED=$((STARTED+1))
else
    FAILED=$((FAILED+1))
fi
if start_agent "fair-assessor" "agents/fair_assessor/fair_assessor_agent.py" "8005"; then
    STARTED=$((STARTED+1))
else
    FAILED=$((FAILED+1))
fi

echo ""
echo "5. Starting data source agents..."
if start_agent "wikipedia" "agents/wikipedia_agent/wikipedia_agent.py" "8010"; then
    STARTED=$((STARTED+1))
else
    FAILED=$((FAILED+1))
fi
if start_agent "arxiv" "agents/arxiv_agent/arxiv_agent.py" "8011"; then
    STARTED=$((STARTED+1))
else
    FAILED=$((FAILED+1))
fi
if start_agent "openlibrary" "agents/openlibrary_agent/openlibrary_agent.py" "8012"; then
    STARTED=$((STARTED+1))
else
    FAILED=$((FAILED+1))
fi
if start_agent "fact-checker" "agents/fact_checker/fact_checker_agent.py" "8013"; then
    STARTED=$((STARTED+1))
else
    FAILED=$((FAILED+1))
fi

echo ""
echo "6. Starting composite agents..."
if start_agent "paper-analyzer" "agents/paper_analyzer/paper_analyzer_agent.py" "8003"; then
    STARTED=$((STARTED+1))
else
    FAILED=$((FAILED+1))
fi
if start_agent "nl-handler" "agents/nl_handler_scientific/nl_handler_agent.py" "8002"; then
    STARTED=$((STARTED+1))
else
    FAILED=$((FAILED+1))
fi

echo ""
echo "7. Starting UI..."
if start_agent "chat-ui" "agents/chat_ui/chat_ui_agent.py" "8001"; then
    STARTED=$((STARTED+1))
else
    FAILED=$((FAILED+1))
fi

echo ""
echo "8. Starting LLM Consultant (Dynamic Workflow Generator)..."
if start_agent "llm-consultant" "agents/llm_consultant/llm_consultant_agent.py" "8014"; then
    STARTED=$((STARTED+1))
else
    FAILED=$((FAILED+1))
fi

echo ""
echo "=========================================="
echo "📊 Startup Summary"
echo "=========================================="
echo "Started: $STARTED agents"
echo "Failed: $FAILED agents"
echo "Already running: $((13 - STARTED - FAILED)) agents"
echo ""
if [ $STARTED -gt 0 ]; then
    echo "✅ Started $STARTED new agent(s)"
fi
if [ $FAILED -gt 0 ]; then
    echo "⚠️  $FAILED agent(s) failed to start"
    echo "   Check logs/ directory for error details"
fi
echo "=========================================="
echo ""
echo "🌐 Web Interface: http://localhost:8001/ui"
echo "📊 Registry Status: http://localhost:8000/"
echo "📝 Logs directory: ./logs/"
echo ""
echo "To stop the system: ./stop_system.sh"
echo "To check status: ./check_status.sh"
echo ""
