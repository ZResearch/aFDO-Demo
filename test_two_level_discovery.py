#!/usr/bin/env python3
"""
Test two-level semantic discovery (operation + aFDO descriptions).
Verifies that queries are matched against both levels and scores are combined.
"""

import httpx
import asyncio
import json


async def test_two_level_discovery():
    """
    Test that semantic discovery matches against:
    1. Operation descriptions
    2. aFDO agent descriptions
    3. Combines scores with simple sum
    """

    registry_url = "http://localhost:8000"

    print("=" * 70)
    print("Testing Two-Level Semantic Discovery")
    print("=" * 70)

    test_cases = [
        {
            "query": "who is the president of Algeria",
            "expected_agent": "Wikipedia Agent",
            "reason": "Factual question about people/leaders"
        },
        {
            "query": "find research papers about quantum computing",
            "expected_agent": "ArXiv Agent",
            "reason": "Research papers query"
        },
        {
            "query": "search for books about machine learning",
            "expected_agent": "Open Library Agent",
            "reason": "Books query"
        },
        {
            "query": "compare Algeria and Morocco",
            "expected_agent": "LLM Consultant",
            "reason": "Synthesis/comparison query"
        }
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, test in enumerate(test_cases, 1):
            print(f"\n{'=' * 70}")
            print(f"Test {i}: {test['query']}")
            print(f"Expected: {test['expected_agent']} ({test['reason']})")
            print(f"{'=' * 70}")

            try:
                response = await client.post(
                    f"{registry_url}/doip/discover/by_operation_query",
                    json={
                        "query": test['query'],
                        "top_k": 3,
                        "min_score": 0.0
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    agents = result.get('data', [])

                    if agents:
                        print(f"\n✅ Found {len(agents)} agents:")
                        for j, agent in enumerate(agents, 1):
                            print(f"\n  {j}. {agent['agent_name']}")
                            print(f"     Agent Score:     {agent['agent_score']:.4f}")
                            print(f"     Operation Score: {agent['operation_score']:.4f}")
                            print(f"     Combined Score:  {agent['combined_score']:.4f}")
                            print(f"     Best Operation:  {agent['best_operation']}")
                            print(f"     Status:          {agent['status']}")
                            print(f"     Reputation:      {agent['reputation']:.3f}")

                        top_agent = agents[0]['agent_name']
                        if top_agent == test['expected_agent']:
                            print(f"\n  ✅ PASS: Top agent is {top_agent}")
                        else:
                            print(f"\n  ⚠️  UNEXPECTED: Top agent is {top_agent}, expected {test['expected_agent']}")
                    else:
                        print(f"\n  ❌ No agents found!")
                else:
                    print(f"\n  ❌ Request failed: {response.status_code}")
                    print(f"     {response.text[:200]}")

            except Exception as e:
                print(f"\n  ❌ Error: {e}")

            await asyncio.sleep(0.5)

    print(f"\n{'=' * 70}")
    print("Testing Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_two_level_discovery())
