#!/usr/bin/env python3
"""Test queries and classify their execution patterns."""
import requests
import json
import time
from pathlib import Path

def send_query(query):
    """Send query to Chat UI and return trace file path."""
    response = requests.post(
        'http://localhost:8001/doip/extend/receive_user_input',
        json={
            'caller_pid': 'pattern_test',
            'operation': 'receive_user_input',
            'parameters': {'message': query}
        }
    )
    
    if response.status_code != 200:
        return None, f"Error: {response.status_code}"
    
    # Get latest trace file
    traces = sorted(Path('/tmp/afdo_traces').glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
    if traces:
        return traces[0], None
    return None, "No trace file found"

def analyze_trace(trace_file):
    """Analyze trace to determine execution pattern."""
    with open(trace_file) as f:
        trace = json.load(f)
    
    summary = trace.get('summary', {})
    events = trace.get('events', [])
    
    # Count delegation steps
    delegations = [e for e in events if e.get('action_type') == 'delegate']
    agents = summary.get('agents_involved', [])
    
    # Determine pattern
    if len(agents) <= 2:  # Chat UI + 1 executor
        pattern = "SIMPLE"
    elif len(agents) >= 4:  # Likely parallel (Chat UI + LLM + multiple sources)
        pattern = "PARALLEL"
    elif len(agents) == 3:  # Chat UI + LLM + executor (could be cascading)
        pattern = "CASCADING"
    else:
        pattern = "UNKNOWN"
    
    return {
        'pattern': pattern,
        'agents': agents,
        'num_agents': len(agents),
        'num_delegations': len(delegations),
        'duration_ms': summary.get('total_duration_ms', 0),
        'status': summary.get('status', 'unknown')
    }

# Test queries
test_queries = [
    # Potential SIMPLE queries (direct to one agent)
    "What is the capital of France?",
    "Who invented the telephone?",
    "When was Python created?",
    
    # Potential CASCADING queries (verification with sources)
    "The 2023 paper claims AI beats humans. Is this true?",
    "A study says coffee is healthy. Verify this claim.",
    "Einstein's theory predicts X. Is this accurate?",
    
    # Potential PARALLEL queries (multi-source verification)
    "Is climate change accelerating? Cross-check multiple sources.",
    "Verify: The moon landing happened in 1969 using multiple sources.",
    "Cross-validate: Water boils at 100°C at sea level.",
]

print("=" * 80)
print("EXECUTION PATTERN TEST")
print("=" * 80)

results = []
for query in test_queries:
    print(f"\n[Testing] {query[:60]}...")
    
    trace_file, error = send_query(query)
    if error:
        print(f"  ❌ {error}")
        continue
    
    time.sleep(1)  # Wait for trace to be written
    
    analysis = analyze_trace(trace_file)
    results.append({
        'query': query,
        'analysis': analysis
    })
    
    print(f"  Pattern: {analysis['pattern']}")
    print(f"  Agents: {', '.join(analysis['agents'])}")
    print(f"  Duration: {analysis['duration_ms']}ms")

# Categorize results
print("\n" + "=" * 80)
print("CATEGORIZED RESULTS")
print("=" * 80)

for pattern_type in ['SIMPLE', 'CASCADING', 'PARALLEL']:
    matches = [r for r in results if r['analysis']['pattern'] == pattern_type]
    print(f"\n{pattern_type} Execution ({len(matches)} found):")
    for r in matches[:2]:  # Show first 2 of each
        print(f"  ✓ {r['query'][:70]}")
        print(f"    Agents: {', '.join(r['analysis']['agents'])}")

