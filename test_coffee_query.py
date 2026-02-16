#!/usr/bin/env python3
"""Test 'what is coffee' with LLM configured."""

import asyncio
import httpx


async def test_coffee_query():
    """Test the coffee question."""
    print("\n" + "="*60)
    print("TEST: 'what is coffee' with LLM configured")
    print("="*60)

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            print("\nSending request...")
            response = await client.post(
                "http://localhost:8001/doip/extend/receive_user_input",
                json={
                    "authentication": {"caller_pid": "test-client"},
                    "parameters": {"message": "what is coffee"}
                }
            )

            print(f"Status: {response.status_code}\n")

            if response.status_code == 200:
                data = response.json()
                result = data.get('data', {})
                message = result.get('message', '')
                status = result.get('status', '')

                print(f"Status: {status}")
                print(f"\nResponse:")
                print("-" * 60)
                print(message)
                print("-" * 60)

                # Check for various outcomes
                if "error" in message.lower() and "encountered an error" in message.lower():
                    print("\n❌ Still getting error (LLM may not be accessible)")
                    return False
                elif "Hello! I'm an autonomous agent" in message:
                    print("\n⚠️ Got old generic fallback message")
                    return False
                else:
                    print("\n✅ Got a real response!")
                    if "sources_used" in result:
                        print(f"   Sources: {result['sources_used']}")
                    if "answered_by" in result:
                        print(f"   Answered by: {result['answered_by']}")
                    return True
            else:
                print(f"❌ HTTP {response.status_code}")
                print(response.text[:500])
                return False

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    result = asyncio.run(test_coffee_query())
    print("\n" + "="*60)
    if result:
        print("🎉 SUCCESS - Dynamic query handling works!")
    else:
        print("⚠️ Issue detected - check logs for details")
    print("="*60 + "\n")
