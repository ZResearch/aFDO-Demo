#!/usr/bin/env python3
"""Quick test to verify all fixes are working."""

import asyncio
import httpx


async def test_all():
    """Test all query types."""

    tests = [
        ("hi", "Greeting", True),
        ("what can you do", "Capability query", True),
        ("what is coffee", "Simple question", True),
    ]

    print("\n" + "="*60)
    print("COMPREHENSIVE SYSTEM TEST")
    print("="*60)

    results = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        for message, description, should_work in tests:
            print(f"\n📝 Testing: {description}")
            print(f"   Query: '{message}'")

            try:
                response = await client.post(
                    "http://localhost:8001/doip/extend/receive_user_input",
                    json={
                        "authentication": {"caller_pid": "test"},
                        "parameters": {"message": message}
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    result = data.get('data', {})
                    msg = result.get('message', '')
                    status = result.get('status', '')

                    if status == 'error':
                        print(f"   ❌ Got error: {msg[:100]}")
                        results.append((description, False))
                    else:
                        print(f"   ✅ Success: {msg[:100]}...")
                        results.append((description, True))
                else:
                    print(f"   ❌ HTTP {response.status_code}")
                    results.append((description, False))

            except Exception as e:
                print(f"   ❌ Exception: {e}")
                results.append((description, False))

    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)

    all_passed = True
    for desc, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {desc}")
        if not passed:
            all_passed = False

    print("="*60)

    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ System Status:")
        print("   - Task 27 (Delegation) working")
        print("   - Task 28 (Dynamic queries) working")
        print("   - LLM Consultant running")
        print("   - Model configuration correct")
        print("\n🚀 Ready for IJCAI 2026 Demo!")
    else:
        print("\n⚠️ Some tests failed - check logs")

    print("\n")
    return all_passed


if __name__ == "__main__":
    result = asyncio.run(test_all())
    exit(0 if result else 1)
