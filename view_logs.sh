#!/bin/bash

# view_logs.sh - View logs from agents

echo "=========================================="
echo "📝 aFDO Agent Logs"
echo "=========================================="
echo ""

if [ $# -eq 0 ]; then
    echo "Available logs:"
    ls -1 logs/*.log 2>/dev/null || echo "No logs found"
    echo ""
    echo "Usage: ./view_logs.sh <agent-name>"
    echo "Example: ./view_logs.sh registry"
    echo ""
    echo "Or view all: ./view_logs.sh all"
else
    if [ "$1" == "all" ]; then
        for log in logs/*.log; do
            if [ -f "$log" ]; then
                echo "=== $(basename $log) ==="
                tail -20 $log
                echo ""
            fi
        done
    else
        logfile="logs/$1.log"
        if [ -f "$logfile" ]; then
            tail -f $logfile
        else
            echo "Log file not found: $logfile"
        fi
    fi
fi
