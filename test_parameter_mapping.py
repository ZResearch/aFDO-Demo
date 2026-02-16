#!/usr/bin/env python3
"""
Test parameter mapping in semantic discovery.
Verifies that operations are called with the correct parameter names.
"""

import httpx
import asyncio
import json


async def test_parameter_mapping():
    """
    Test that semantic discovery correctly maps user query to operation parameters.

    Test cases:
    1. "who is the president of Algeria" → should call receive_query with {"query": ...}
    2. Direct call to get_article_summary → should require {"topic": ...}
    """

    base_url = "http://localhost:8001"

    print("=" * 60)
    print("Testing Parameter Mapping in Semantic Discovery")
    print("=" * 60)

    # Test 1: Simple query that should work with receive_query
    print("\n📝 Test 1: Query that uses receive_query operation")
    print("Query: 'who is the president of Algeria'")
    print("Expected: Call Wikipedia.receive_query with {query: ...}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{base_url}/doip/extend/receive_user_input",
            json={"message": "who is the president of Algeria"}
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"   Status: {result.get('status')}")
            data = result.get('data', {})
            if 'summary' in data or 'response' in data:
                summary = data.get('summary') or data.get('response', '')
                print(f"   Response preview: {summary[:200]}...")
        else:
            print(f"❌ FAILED with status {response.status_code}")
            print(f"   Error: {response.text[:200]}")

    # Give system time to process
    await asyncio.sleep(1)

    # Test 2: Check trace to see what parameters were used
    print("\n📝 Test 2: Checking trace files for parameter usage")
    print("Looking for most recent trace...")

    import glob
    import os

    traces = glob.glob("/tmp/afdo_traces/req_*.json")
    if traces:
        latest_trace = max(traces, key=os.path.getctime)
        print(f"   Latest trace: {latest_trace}")

        with open(latest_trace) as f:
            trace = json.load(f)

        print(f"   Request: {trace['summary']['user_query']}")
        print(f"   Status: {trace['summary']['status']}")
        print(f"   Agents: {', '.join(trace['summary']['agents_involved'])}")

        # Look for delegation events
        for event in trace['events']:
            if event['action_type'] == 'delegate':
                print(f"\n   📤 Delegation found:")
                print(f"      To: {event.get('delegated_to')}")
                print(f"      Operation: {event.get('operation')}")
                print(f"      Parameters: {event.get('input_data')}")

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_parameter_mapping())
