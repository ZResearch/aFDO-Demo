"""
Verify that all agents register correctly with the registry.
"""

import asyncio
import httpx
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def verify_registrations():
    """Verify all agents are registered."""

    print("\n" + "="*60)
    print("VERIFYING AGENT REGISTRATIONS")
    print("="*60)

    registry_url = "http://localhost:8000"

    # Wait for registry to be ready
    print("\n⏳ Waiting for registry...")
    await asyncio.sleep(2)

    # Expected agents
    expected_agents = [
        ("Wikipedia Agent", "21.T11148/type-data-source-v1", 8010),
        ("ArXiv Agent", "21.T11148/type-data-source-v1", 8011),
        ("Open Library Agent", "21.T11148/type-data-source-v1", 8012),
        ("LLM Consultant", "21.T11148/type-consultant-v1", 8014)
    ]

    print("\n📋 Checking registrations...")
    print("-" * 60)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get all active FDOs
            response = await client.get(f"{registry_url}/doip/search/fdos/active")
            all_agents = response.json().get("data", [])

            for name, fdo_type, port in expected_agents:
                # Check if our agent is in the list
                found = False
                for agent in all_agents:
                    agent_name = agent.get("kernel_attributes", {}).get("name", "")
                    agent_port = agent.get("kernel_attributes", {}).get("port", 0)

                    if agent_name == name and agent_port == port:
                        found = True
                        print(f"✅ {name:25} Type: {fdo_type:40} Port: {port}")
                        break

                if not found:
                    print(f"❌ {name:25} NOT REGISTERED")

    except Exception as e:
        print(f"❌ Error checking registrations: {e}")

    print("-" * 60)

    # Test operation discovery
    print("\n🔍 Testing Operation Discovery...")
    print("-" * 60)

    test_operations = [
        "get_article_summary",
        "search_papers",
        "search_books",
        "generate_workflow"
    ]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            for operation in test_operations:
                try:
                    # Search for agents with this operation
                    response = await client.get(f"{registry_url}/doip/search/fdos/active")
                    all_agents = response.json().get("data", [])

                    # Filter agents that have this operation
                    agents_with_op = [
                        a for a in all_agents
                        if operation in a.get("operations", []) or operation in a.get("operation_pids", [])
                    ]

                    if agents_with_op:
                        print(f"✅ {operation:30} → {len(agents_with_op)} agent(s) found")
                        for agent in agents_with_op:
                            agent_name = agent.get("kernel_attributes", {}).get("name", "unknown")
                            agent_cost = agent.get("kernel_attributes", {}).get("cost", 0)
                            print(f"   - {agent_name} (${agent_cost:.3f})")
                    else:
                        print(f"❌ {operation:30} → No agents found")

                except Exception as e:
                    print(f"❌ {operation:30} → ERROR: {e}")

    except Exception as e:
        print(f"❌ Error in operation discovery: {e}")

    print("-" * 60)

    print("\n" + "="*60)
    print("✅ VERIFICATION COMPLETE")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(verify_registrations())
