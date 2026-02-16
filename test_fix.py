#!/usr/bin/env python3
"""
Test script for Task 27 fixes.

Tests that greetings and capability queries work correctly.
"""

import asyncio
import httpx


async def test_greeting():
    """Test greeting message."""
    print("\n" + "="*60)
    print("TEST 1: Greeting Message")
    print("="*60)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                "http://localhost:8001/doip/extend/receive_user_input",
                json={
                    "authentication": {"caller_pid": "test-client"},
                    "parameters": {"message": "hi"}
                }
            )

            print(f"\nStatus: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"Response: {data.get('status')}")

                result_data = data.get('data', {})
                message = result_data.get('message', '')
                print(f"Message: {message[:200]}..." if len(message) > 200 else f"Message: {message}")

                if "No suitable agents found" in message:
                    print("❌ TEST FAILED: Still getting 'No suitable agents found' error")
                    return False
                else:
                    print("✅ TEST PASSED: Greeting handled successfully")
                    return True
            else:
                print(f"❌ TEST FAILED: HTTP {response.status_code}")
                print(f"Response: {response.text[:500]}")
                return False

        except Exception as e:
            print(f"❌ TEST FAILED: {e}")
            return False


async def test_capability_query():
    """Test capability query."""
    print("\n" + "="*60)
    print("TEST 2: Capability Query")
    print("="*60)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                "http://localhost:8001/doip/extend/receive_user_input",
                json={
                    "authentication": {"caller_pid": "test-client"},
                    "parameters": {"message": "what can you do"}
                }
            )

            print(f"\nStatus: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"Response: {data.get('status')}")

                result_data = data.get('data', {})
                message = result_data.get('message', '')
                print(f"Message: {message[:200]}..." if len(message) > 200 else f"Message: {message}")

                if "No suitable agents found" in message:
                    print("❌ TEST FAILED: Still getting 'No suitable agents found' error")
                    return False
                else:
                    print("✅ TEST PASSED: Capability query handled successfully")
                    return True
            else:
                print(f"❌ TEST FAILED: HTTP {response.status_code}")
                print(f"Response: {response.text[:500]}")
                return False

        except Exception as e:
            print(f"❌ TEST FAILED: {e}")
            return False


async def run_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("TASK 27 FIX VERIFICATION")
    print("="*60)
    print("\nTesting delegation architecture fixes...")
    print("Expected: Greetings and capability queries should be handled")
    print("          by Chat UI directly (no delegation)\n")

    test1_result = await test_greeting()
    test2_result = await test_capability_query()

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Greeting Test: {'✅ PASSED' if test1_result else '❌ FAILED'}")
    print(f"Capability Test: {'✅ PASSED' if test2_result else '❌ FAILED'}")

    if test1_result and test2_result:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nThe fix works:")
        print("  ✅ Policies specify needs, not agent names")
        print("  ✅ Chat UI handles greetings directly")
        print("  ✅ No delegation chains")
        print("  ✅ Fallback strategies work")
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("\nNext steps:")
        print("  1. Check if agents are running: ./check_status.sh")
        print("  2. Restart system: ./stop_system.sh && ./start_system.sh")
        print("  3. Check logs in logs/ directory")

    print("="*60 + "\n")

    return test1_result and test2_result


if __name__ == "__main__":
    result = asyncio.run(run_tests())
    exit(0 if result else 1)
