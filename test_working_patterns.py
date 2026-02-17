#!/usr/bin/env python3
import requests, json, time
from pathlib import Path

def test_query(query, timeout=60):
    print(f"\nTesting: {query[:70]}...")
    
    try:
        response = requests.post(
            'http://localhost:8001/doip/extend/receive_user_input',
            json={'caller_pid': 'test', 'operation': 'receive_user_input',
                  'parameters': {'message': query}},
            timeout=timeout
        )
        
        if response.status_code != 200:
            return None, f"HTTP {response.status_code}"
            
        time.sleep(1)
        
        # Get trace
        traces = sorted(Path('/tmp/afdo_traces').glob('*.json'), 
                       key=lambda p: p.stat().st_mtime, reverse=True)
        if not traces:
            return None, "No trace"
            
        with open(traces[0]) as f:
            trace = json.load(f)
        
        summary = trace['summary']
        agents = summary['agents_involved']
        status = summary['status']
        events = trace.get('events', [])
        
        # Count parallel delegations (same timestamp different agents)
        delegations = [e for e in events if e.get('action_type') == 'delegate']
        parallel_groups = []
        if delegations:
            current_group = [delegations[0]]
            for i in range(1, len(delegations)):
                time_diff = abs(float(delegations[i]['timestamp'].split('T')[1].replace('Z','')) - 
                              float(delegations[i-1]['timestamp'].split('T')[1].replace('Z','')))
                if time_diff < 0.1:  # Within 0.1s = parallel
                    current_group.append(delegations[i])
                else:
                    if len(current_group) > 1:
                        parallel_groups.append(current_group)
                    current_group = [delegations[i]]
            if len(current_group) > 1:
                parallel_groups.append(current_group)
        
        # Determine pattern
        if len(parallel_groups) > 0:
            pattern = "PARALLEL"
            detail = f"{len(agents)} agents, {len(parallel_groups)} parallel groups"
        elif len(agents) >= 4:
            pattern = "CASCADING (4+ layers)"
            detail = f"{len(agents)} agents in sequence"
        elif len(agents) == 3:
            pattern = "CASCADING (3 layers)"
            detail = "Chat UI → LLM → Executor"
        else:
            pattern = "SIMPLE"
            detail = f"{len(agents)} agents"
        
        result = {
            'query': query,
            'pattern': pattern,
            'detail': detail,
            'agents': agents,
            'status': status,
            'delegations': len(delegations)
        }
        
        if status == 'success':
            print(f"  ✅ {pattern} - {detail} - {status}")
        else:
            print(f"  ⚠️  {pattern} - {detail} - {status}")
            
        return result, None
        
    except Exception as e:
        return None, str(e)

# Test different query types
queries = {
    "Simple factual (CASCADING expected)": [
        "What is Paris?",
        "Who is Einstein?",
    ],
    "Verification (PARALLEL expected)": [
        "Is Paris the capital of France?",
        "Did Einstein win a Nobel Prize?",
        "The claim states water boils at 100C. True or false?",
        "Verify: The Earth orbits the Sun.",
    ],
}

results = {"SIMPLE": [], "CASCADING": [], "PARALLEL": []}

for category, query_list in queries.items():
    print(f"\n{'='*80}")
    print(f"{category}")
    print('='*80)
    
    for q in query_list:
        result, error = test_query(q, timeout=90)
        if error:
            print(f"  ❌ Error: {error}")
        elif result and result['status'] == 'success':
            pattern_key = result['pattern'].split()[0]  # Get first word
            if pattern_key in results:
                results[pattern_key].append(result)
        time.sleep(2)

# Final summary
print(f"\n{'='*80}")
print("SUCCESSFUL QUERIES BY PATTERN")
print('='*80)

for pattern_type in ["SIMPLE", "CASCADING", "PARALLEL"]:
    matches = results[pattern_type]
    print(f"\n{pattern_type} ({len(matches)} found):")
    for r in matches[:2]:
        print(f"  ✓ {r['query'][:65]}")
        print(f"    {r['detail']}, agents: {r['agents']}")

