#!/bin/bash

echo "======================================"
echo "Testing Monitoring Fixes"
echo "======================================"
echo ""

echo "1. Testing Chat UI Agent Discovery"
echo "-----------------------------------"

# Test via the chat UI endpoint using proper DOIP format
echo "Sending 'hello' message..."
curl -s -X POST "http://localhost:8001/doip/extend/receive_user_input" \
  -H "Content-Type: application/json" \
  -d '{
    "caller_pid": "test-user",
    "parameters": {
      "message": "hello",
      "budget": 1.0
    }
  }' | python3 -c "import json, sys; data=json.load(sys.stdin); print('Status:', data.get('status')); msg = data.get('data', {}).get('message', ''); print('Message preview:', msg[:200] if len(msg) > 200 else msg)"

echo ""
echo "2. Check Chat UI logs for agent discovery"
echo "-----------------------------------"
tail -50 logs/chat-ui.log | grep -A 5 -B 5 "agent"

echo ""
echo "3. Test Monitor Endpoints"
echo "-----------------------------------"
echo "Testing /market/agents/all..."
curl -s "http://localhost:8000/market/agents/all" | python3 -c "import json, sys; data=json.load(sys.stdin); print(f\"Found {len(data.get('data', []))} agents\")"

echo ""
echo "Testing FDO details fetch..."
curl -s "http://localhost:8000/doip/read/fdo/21.T11148%2Fafdo-pdf-parser" | python3 -c "import json, sys; data=json.load(sys.stdin).get('data', {}); ka = data.get('kernel_attributes', {}); print(f\"Name: {ka.get('name', 'N/A')}, Port: {ka.get('port', 'N/A')}\")"

echo ""
echo "======================================"
echo "Test complete!"
echo "======================================"
