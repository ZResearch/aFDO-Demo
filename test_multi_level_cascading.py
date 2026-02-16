"""
Test Multi-Level Cascading Delegation

Demonstrates:
1. User → Chat UI (SEMANTIC_DISCOVERY)
2. Chat UI → Wikipedia (receives synthesis query)
3. Wikipedia policy detects synthesis needed → SEMANTIC_DISCOVERY
4. Wikipedia → LLM Consultant (for synthesis)
5. LLM Consultant synthesizes answer
6. Results cascade back: LLM → Wikipedia → Chat UI → User

This is TRUE multi-level cascading with 3 levels of delegation.
"""

import asyncio
import httpx
import json
import time


async def test_multi_level_cascading():
    """
    Test multi-level cascading with a synthesis query.

    Query: "Compare Algeria and Morocco"

    Expected flow:
    1. Chat UI receives query
    2. Chat UI delegates to Wikipedia (best match for "Algeria")
    3. Wikipedia receives "Compare Algeria and Morocco"
    4. Wikipedia policy detects "compare" → query_requires_synthesis = True
    5. Wikipedia triggers SEMANTIC_DISCOVERY
    6. Wikipedia discovers LLM Consultant
    7. Wikipedia delegates to LLM Consultant
    8. LLM synthesizes comparison
    9. Results cascade back through the chain
    """

    print("="*80)
    print("MULTI-LEVEL CASCADING DELEGATION TEST")
    print("="*80)
    print()
    print("Query: 'Compare Algeria and Morocco - which is larger?'")
    print()
    print("Expected Cascade:")
    print("  User")
    print("    ↓")
    print("  Chat UI (SEMANTIC_DISCOVERY)")
    print("    ↓")
    print("  Wikipedia (detects synthesis query)")
    print("    ↓")
    print("  Wikipedia Policy: query_requires_synthesis = True → SEMANTIC_DISCOVERY")
    print("    ↓")
    print("  LLM Consultant (synthesizes comparison)")
    print("    ↓")
    print("  Results cascade back:")
    print("  LLM → Wikipedia → Chat UI → User")
    print()
    print("="*80)
    print()

    # Wait for system to be ready
    print("⏳ Waiting for system to be ready...")
    await asyncio.sleep(2)

    # Test query that requires synthesis (compare)
    query = "Compare Algeria and Morocco - which is larger?"

    print(f"📤 Sending query: '{query}'")
    print()

    start_time = time.time()

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "http://localhost:8001/doip/extend/receive_user_input",
                json={
                    "caller_pid": "test-client",
                    "parameters": {
                        "message": query
                    }
                }
            )

            result = response.json()
            duration = time.time() - start_time

            print("="*80)
            print("RESULT")
            print("="*80)
            print()

            if response.status_code == 200:
                print(f"✅ Status: SUCCESS")
                print(f"⏱️  Duration: {duration:.2f}s")
                print()

                # Extract response
                if isinstance(result, dict):
                    if 'data' in result:
                        data = result['data']
                        if isinstance(data, dict):
                            response_text = data.get('response', data.get('answer', data.get('summary', str(data))))
                            print(f"📨 Response:")
                            print(f"   {response_text[:500]}")
                            if len(response_text) > 500:
                                print(f"   ... (truncated, {len(response_text)} chars total)")
                        else:
                            print(f"📨 Data: {data}")
                    elif 'response' in result:
                        print(f"📨 Response: {result['response'][:500]}")
                    else:
                        print(f"📨 Result: {json.dumps(result, indent=2)[:500]}")

                    # Check trace for multi-level cascading
                    print()
                    print("-"*80)
                    print("TRACE ANALYSIS")
                    print("-"*80)
                    print()

                    trace = result.get('_trace', {})
                    trace_file = trace.get('trace_file')

                    if trace_file:
                        print(f"📊 Trace file: {trace_file}")

                        # Load and analyze trace
                        try:
                            with open(trace_file, 'r') as f:
                                trace_data = json.load(f)

                            events = trace_data.get('events', [])

                            print(f"📋 Total events: {len(events)}")
                            print()

                            # Identify agents involved
                            agents = set()
                            delegations = []

                            for event in events:
                                agent_name = event.get('agent_name', 'Unknown')
                                agents.add(agent_name)

                                if event.get('action_type') == 'delegate':
                                    delegated_to = event.get('delegated_to', 'Unknown')
                                    delegations.append((agent_name, delegated_to))

                            print(f"👥 Agents involved: {', '.join(sorted(agents))}")
                            print()

                            if delegations:
                                print("🔗 Delegation chain:")
                                for i, (from_agent, to_agent) in enumerate(delegations, 1):
                                    print(f"   {i}. {from_agent} → {to_agent}")

                                # Check for multi-level
                                if len(delegations) >= 2:
                                    print()
                                    print("✅ MULTI-LEVEL CASCADING DETECTED!")
                                    print(f"   Depth: {len(delegations)} levels")
                                else:
                                    print()
                                    print("⚠️  Only single-level delegation detected")
                            else:
                                print("❌ No delegations found in trace")

                        except FileNotFoundError:
                            print(f"⚠️  Trace file not found: {trace_file}")
                        except Exception as e:
                            print(f"⚠️  Error reading trace: {e}")
                    else:
                        print("⚠️  No trace file in result")

            else:
                print(f"❌ Status: FAILED")
                print(f"   HTTP {response.status_code}")
                print(f"   Error: {result}")

            print()
            print("="*80)

    except httpx.ConnectError:
        print()
        print("❌ ERROR: Cannot connect to Chat UI (port 8001)")
        print("   Make sure the system is running: ./start_system.sh")
        print()
    except Exception as e:
        print()
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        print()


async def main():
    """Run test."""
    print()
    await test_multi_level_cascading()
    print()


if __name__ == "__main__":
    asyncio.run(main())
