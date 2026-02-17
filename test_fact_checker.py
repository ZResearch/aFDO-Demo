#!/usr/bin/env python3
import requests
import time
import json
from pathlib import Path

def test_and_analyze(query):
    print(f"\n{'='*80}")
    print(f"Testing: {query}")
    print('='*80)
    
    response = requests.post(
        'http://localhost:8001/doip/extend/receive_user_input',
        json={'caller_pid': 'test', 'operation': 'receive_user_input', 
              'parameters': {'message': query}}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed: {response.status_code}")
        return None
    
    time.sleep(2)
    
    # Check logs for routing
    import subprocess
    result = subprocess.run(
        ['tail', '-50', 'logs/chat-ui.log'],
        capture_output=True, text=True
    )
    
    lines = result.stdout.split('\n')
    for i, line in enumerate(lines):
        if 'step2_find_executor' in line and i+1 < len(lines):
            # Next line should have the discovery query
            if i+1 < len(lines) and 'Operation-based discovery' in lines[i+1]:
                print(f"\n📋 Step2 capability query:")
                print(f"  {lines[i+1].split('discovery:')[1].split('→')[0].strip()[:100]}")
            if i+2 < len(lines):
                print(f"\n🎯 Selected agent:")
                for j in range(i+1, min(i+5, len(lines))):
                    if 'Found:' in lines[j]:
                        print(f"  {lines[j].strip()}")
                        break
    
    # Get trace
    traces = sorted(Path('/tmp/afdo_traces').glob('*.json'), 
                    key=lambda p: p.stat().st_mtime, reverse=True)
    if traces:
        with open(traces[0]) as f:
            trace = json.load(f)
        agents = trace['summary']['agents_involved']
        print(f"\n📊 Execution chain: {' → '.join(agents)}")
        return len(agents), agents
    return None, None

# Test queries - focus on CLAIM VERIFICATION
verification_queries = [
    "A recent paper claims neural networks are better than humans. Is this claim verified?",
    "The study states that exercise prevents disease. Verify this claim with evidence.",
    "Research claims quantum computers will break encryption. Is this claim accurate?",
    "The article asserts that AI is conscious. Validate this claim.",
]

print("Testing VERIFICATION queries (should trigger Fact Checker + parallel sources):")
results = []
for q in verification_queries:
    layers, agents = test_and_analyze(q)
    if layers:
        results.append((q, layers, agents))
    time.sleep(2)

print("\n" + "="*80)
print("SUMMARY OF RESULTS")
print("="*80)

for q, layers, agents in results:
    if layers >= 5:
        print(f"✅ PARALLEL ({layers} layers): {q[:60]}...")
    elif layers == 3:
        print(f"⚠️  CASCADING ({layers} layers): {q[:60]}...")
    print(f"   Agents: {agents}")

