#!/bin/bash
# Quick verification script for activity logs

echo "=========================================="
echo "ACTIVITY LOGS VERIFICATION"
echo "=========================================="
echo ""

# Check if agents are running
echo "1. Checking if agents are running..."
if ! curl -s http://localhost:8000/ > /dev/null; then
    echo "   ❌ Registry not running on port 8000"
    exit 1
fi
echo "   ✅ Registry is running"

if ! curl -s http://localhost:8001/ > /dev/null; then
    echo "   ⚠️  NL Handler not running on port 8001"
else
    echo "   ✅ NL Handler is running"
fi

if ! curl -s http://localhost:8003/ > /dev/null; then
    echo "   ⚠️  Paper Analyzer not running on port 8003"
else
    echo "   ✅ Paper Analyzer is running"
fi

if ! curl -s http://localhost:8004/ > /dev/null; then
    echo "   ⚠️  PDF Parser not running on port 8004"
else
    echo "   ✅ PDF Parser is running"
fi

echo ""
echo "2. Making a test request to trigger activity logging..."
curl -s -X POST http://localhost:8001/doip/extend/receive_user_input \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"message": "Analyze test paper"}}' > /dev/null

if [ $? -eq 0 ]; then
    echo "   ✅ Request sent successfully"
else
    echo "   ❌ Request failed"
    exit 1
fi

echo ""
echo "3. Waiting 6 seconds for activity log sync..."
sleep 6

echo ""
echo "4. Checking Paper Analyzer's activity log..."
if [ -f "registry/data/fdos/21.T11148-afdo-paper-analyzer.json" ]; then
    echo "   📄 FDO record found"
    echo ""
    echo "   Activity Log Contents:"
    cat registry/data/fdos/21.T11148-afdo-paper-analyzer.json | jq '.activity_log' 2>/dev/null

    if [ $? -eq 0 ]; then
        echo ""
        # Count calls
        CALLS_MADE=$(cat registry/data/fdos/21.T11148-afdo-paper-analyzer.json | jq '.activity_log.calls_made | length' 2>/dev/null)
        CALLS_RECEIVED=$(cat registry/data/fdos/21.T11148-afdo-paper-analyzer.json | jq '.activity_log.calls_received | length' 2>/dev/null)

        echo "   📊 Calls made: $CALLS_MADE"
        echo "   📊 Calls received: $CALLS_RECEIVED"

        if [ "$CALLS_MADE" -gt 0 ] || [ "$CALLS_RECEIVED" -gt 0 ]; then
            echo ""
            echo "   ✅ Activity logs are working!"
        else
            echo ""
            echo "   ⚠️  Activity logs are empty"
        fi
    else
        echo "   ⚠️  Could not parse activity log (jq not installed or invalid JSON)"
    fi
else
    echo "   ❌ FDO record not found"
    exit 1
fi

echo ""
echo "=========================================="
echo "VERIFICATION COMPLETE"
echo "=========================================="
