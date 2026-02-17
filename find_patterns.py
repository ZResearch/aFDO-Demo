#!/usr/bin/env python3
import requests
import json
import time
from pathlib import Path

def test_query(query, expected_pattern):
    """Test a query and check its execution pattern."""
    print(f"\n{'='*80}")
    print(f"Query: {query}")
    print(f"Expected: {expected_pattern}")
    print('='*80)
    
    # Send query
    response = requests.post(
        'http://localhost:8001/doip/extend/receive_user_input',
        json={
            'caller_pid': 'pattern_test',
            'operation': 'receive_user_input',
            'parameters': {'message': query}
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Request failed: {response.status_code}")
        return None
    
    time.sleep(2)
    
    # Get latest trace
    traces = sorted(Path('/tmp/afdo_traces').glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not traces:
        print("❌ No trace found")
        return None
    
    with open(traces[0]) as f:
        trace = json.load(f)
    
    summary = trace['summary']
    events = trace['events']
    
    agents = summary['agents_involved']
    delegations = [e for e in events if e.get('action_type') == 'delegate']
    
    print(f"\n📊 Execution Details:")
    print(f"  Agents involved: {agents}")
    print(f"  Total agents: {len(agents)}")
    print(f"  Delegation steps: {len(delegations)}")
    print(f"  Duration: {summary['total_duration_ms']}ms")
    
    # Analyze pattern
    if len(agents) >= 5:
        pattern = "PARALLEL (4+ layers)"
    elif len(agents) == 3:
        pattern = "CASCADING (3 layers)"
    elif len(agents) == 2:
        pattern = "SIMPLE (2 layers)"
    else:
        pattern = f"UNKNOWN ({len(agents)} layers)"
    
    print(f"\n🔍 Pattern: {pattern}")
    
    # Show delegation chain
    print(f"\n📋 Delegation Chain:")
    for i, event in enumerate(events):
        if event.get('action_type') == 'delegate':
            print(f"  {i}. {event['agent_name']} → {event['delegated_to']} ({event['operation']})")
    
    return pattern

# Test different query types
queries = {
    "PARALLEL": [
        "Is it true that the Earth is round? Verify with multiple sources.",
        "Verify: Water freezes at 0°C. Cross-check multiple sources.",
        "The study claims coffee is healthy. Is this supported by multiple sources?",
    ],
    "CASCADING": [
        "What is the capital of Germany?",
        "When was the Eiffel Tower built?",
    ],
}

results = {"SIMPLE": [], "CASCADING": [], "PARALLEL": []}

for expected, query_list in queries.items():
    for query in query_list:
        pattern = test_query(query, expected)
        if pattern:
            # Extract category
            if "SIMPLE" in pattern:
                results["SIMPLE"].append(query)
            elif "PARALLEL" in pattern:
                results["PARALLEL"].append(query)
            elif "CASCADING" in pattern:
                results["CASCADING"].append(query)
        time.sleep(1)

print("\n" + "="*80)
print("FINAL RESULTS")
print("="*80)

for pattern_type in ["SIMPLE", "CASCADING", "PARALLEL"]:
    print(f"\n{pattern_type} ({len(results[pattern_type])} found):")
    for q in results[pattern_type][:2]:
        print(f"  ✓ {q}")

