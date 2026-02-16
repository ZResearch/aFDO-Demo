#!/bin/bash

# check_status.sh - Check status of all aFDO agents

echo "=========================================="
echo "📊 aFDO System Status"
echo "=========================================="
echo ""

# Check if agent is running
check_agent() {
    local name=$1
    local port=$2
    local pidfile="logs/$name.pid"

    if [ -f "$pidfile" ]; then
        local pid=$(cat $pidfile)
        if ps -p $pid > /dev/null 2>&1; then
            # Check if port is listening
            if nc -z localhost $port 2>/dev/null; then
                echo "✅ $name (port $port) - RUNNING (PID $pid)"
            else
                echo "⚠️  $name (port $port) - Process alive but port not responding"
            fi
        else
            echo "❌ $name (port $port) - NOT RUNNING (stale PID)"
        fi
    else
        echo "❌ $name (port $port) - NOT RUNNING (no PID file)"
    fi
}

# Check all agents
check_agent "registry" "8000"
check_agent "chat-ui" "8001"
check_agent "nl-handler" "8002"
check_agent "paper-analyzer" "8003"
check_agent "pdf-parser" "8004"
check_agent "fair-assessor" "8005"
check_agent "creator" "8006"
check_agent "llm-gpt4" "8007"
check_agent "llm-gpt4-mini" "8008"
check_agent "wikipedia" "8010"
check_agent "arxiv" "8011"
check_agent "openlibrary" "8012"

echo ""
echo "----------------------------------------"

# Count running agents
running=0
for pidfile in logs/*.pid; do
    if [ -f "$pidfile" ]; then
        pid=$(cat $pidfile)
        if ps -p $pid > /dev/null 2>&1; then
            ((running++))
        fi
    fi
done

echo "Running: $running / 12 agents"
echo ""

if [ $running -eq 12 ]; then
    echo "🌐 Web Interface: http://localhost:8001/ui"
    echo "📊 Registry: http://localhost:8000/"
fi

echo ""
