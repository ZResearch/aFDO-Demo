#!/bin/bash

# stop_system.sh - Stop all aFDO agents
# Improved version with better process detection

echo "=========================================="
echo "🛑 Stopping aFDO Demo System"
echo "=========================================="
echo ""

# Function to stop an agent by port
stop_by_port() {
    local name=$1
    local port=$2
    local stopped=0

    # First try to find process by port
    local pid=$(lsof -ti :$port 2>/dev/null | head -1)

    if [ -n "$pid" ]; then
        echo "Stopping $name (port $port, PID $pid)..."
        kill $pid 2>/dev/null || kill -9 $pid 2>/dev/null || true
        sleep 0.5

        # Verify it stopped
        if ps -p $pid > /dev/null 2>&1; then
            echo "  ⚠️  Process still running, force killing..."
            kill -9 $pid 2>/dev/null || true
            sleep 0.5
        fi

        if ps -p $pid > /dev/null 2>&1; then
            echo "  ❌ Failed to stop"
        else
            echo "  ✅ Stopped"
            stopped=1
        fi

        # Remove PID file
        local pidfile="logs/$name.pid"
        rm -f "$pidfile"
    else
        # No process on port - check PID file
        local pidfile="logs/$name.pid"
        if [ -f "$pidfile" ]; then
            local stored_pid=$(cat $pidfile)
            if ps -p $stored_pid > /dev/null 2>&1; then
                echo "Stopping $name (PID $stored_pid from file)..."
                kill $stored_pid 2>/dev/null || kill -9 $stored_pid 2>/dev/null || true
                sleep 0.5
                echo "  ✅ Stopped"
                stopped=1
            fi
            rm -f "$pidfile"
        fi
    fi

    if [ $stopped -eq 0 ]; then
        echo "$name (port $port): not running"
    fi

    return $stopped
}

# Stop in reverse order (UI first, registry last)
STOPPED=0

stop_by_port "llm-consultant" "8014" && STOPPED=$((STOPPED+1))
stop_by_port "chat-ui" "8001" && STOPPED=$((STOPPED+1))
stop_by_port "nl-handler" "8002" && STOPPED=$((STOPPED+1))
stop_by_port "paper-analyzer" "8003" && STOPPED=$((STOPPED+1))
stop_by_port "openlibrary" "8012" && STOPPED=$((STOPPED+1))
stop_by_port "arxiv" "8011" && STOPPED=$((STOPPED+1))
stop_by_port "wikipedia" "8010" && STOPPED=$((STOPPED+1))
stop_by_port "fair-assessor" "8005" && STOPPED=$((STOPPED+1))
stop_by_port "pdf-parser" "8004" && STOPPED=$((STOPPED+1))
stop_by_port "llm-gpt4-mini" "8008" && STOPPED=$((STOPPED+1))
stop_by_port "llm-gpt4" "8007" && STOPPED=$((STOPPED+1))
stop_by_port "creator" "8006" && STOPPED=$((STOPPED+1))
stop_by_port "registry" "8000" && STOPPED=$((STOPPED+1))

# Final cleanup - catch any stragglers by pattern
echo ""
echo "Checking for remaining agent processes..."

# More aggressive patterns to catch all variations
REMAINING=0

for pattern in \
    "registry/main.py" \
    "creator_agent.py" \
    "llm_endpoint_agent.py" \
    "pdf_parser_agent.py" \
    "fair_assessor_agent.py" \
    "wikipedia_agent.py" \
    "arxiv_agent.py" \
    "openlibrary_agent.py" \
    "paper_analyzer_agent.py" \
    "nl_handler_agent.py" \
    "chat_ui_agent.py" \
    "llm_consultant_agent.py"
do
    if pgrep -f "$pattern" > /dev/null 2>&1; then
        echo "  Found remaining process: $pattern"
        pkill -9 -f "$pattern" 2>/dev/null || true
        REMAINING=$((REMAINING+1))
    fi
done

if [ $REMAINING -gt 0 ]; then
    sleep 1
    echo "  ✅ Killed $REMAINING remaining process(es)"
else
    echo "  ✅ No remaining processes"
fi

# Clean up all PID files
echo ""
echo "Cleaning up PID files..."
rm -f logs/*.pid 2>/dev/null || true
echo "  ✅ PID files cleaned"

echo ""
echo "=========================================="
echo "📊 Shutdown Summary"
echo "=========================================="
echo "Stopped: $STOPPED agents"
echo "Cleaned up: $REMAINING straggler(s)"
echo ""
echo "✅ System stopped"
echo "=========================================="
echo ""
