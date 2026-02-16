#!/bin/bash

# Demo script to show centralized logging in action

echo "🎬 Centralized Logging Demo"
echo "================================"
echo ""

# Check if log file exists
if [ -f "logs/system.log" ]; then
    echo "📋 Previous log file exists. Backing up..."
    timestamp=$(date +%Y%m%d-%H%M%S)
    cp logs/system.log "logs/system-backup-${timestamp}.log"
    echo "✅ Backup created: logs/system-backup-${timestamp}.log"
fi

echo ""
echo "🧪 Running logging test..."
python3 test_logging.py

echo ""
echo "📝 Log file contents:"
echo "================================"
cat logs/system.log

echo ""
echo "================================"
echo "✅ Demo complete!"
echo ""
echo "📖 View logs:"
echo "  - Full log: cat logs/system.log"
echo "  - Live: tail -f logs/system.log"
echo "  - Specific agent: grep 'Test Agent' logs/system.log"
echo "  - Errors only: grep 'ERROR' logs/system.log"
echo ""
echo "📚 Complete documentation: LOGGING.md"
