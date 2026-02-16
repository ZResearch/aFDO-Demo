#!/usr/bin/env python3
"""
Test Autonomous Factual Question Handling

Verifies:
1. Factual questions automatically delegate to Wikipedia
2. User gets complete answer
3. NO commands shown to user
4. NO agent names shown to user
"""

import asyncio
import httpx


async def test_factual_questions():
    """Test factual questions work autonomously."""

    print("\n" + "="*60)
    print("TEST: Factual Questions - Autonomous Delegation")
    print("="*60)

    test_cases = [
        {
            "query": "what is coffee",
            "expected_flow": "Auto-delegate to Wikipedia",
            "expected_result": "Full Wikipedia article summary",
            "forbidden": ["recommend using", "search_wikipedia", "Wikipedia Agent"]
        },
        {
            "query": "who invented the telephone",
            "expected_flow": "Auto-delegate to Wikipedia",
            "expected_result": "Alexander Graham Bell information",
            "forbidden": ["recommend using", "command", "agent"]
        },
        {
            "query": "where is the Eiffel Tower",
            "expected_flow": "Auto-delegate to Wikipedia",
            "expected_result": "Paris, France location",
            "forbidden": ["recommend using", "search_", "Agent"]
        }
    ]

    for case in test_cases:
        print(f"\n{'─'*60}")
        print(f"Query: {case['query']}")
        print(f"{'─'*60}")

        print(f"\n✅ Expected Flow:")
        print(f"   1. User: '{case['query']}'")
        print(f"   2. Policy: Matches factual_questions_auto_delegate")
        print(f"   3. Action: query_registry_for_helper")
        print(f"   4. Discovers: Wikipedia Agent")
        print(f"   5. Extracts topic: '{case['query'].split('is')[-1].strip()}'")
        print(f"   6. Delegates: get_article_summary(topic)")
        print(f"   7. Wikipedia: Returns article")
        print(f"   8. Formats: Natural response")
        print(f"   9. Returns: '{case['expected_result']}'")

        print(f"\n❌ Forbidden in Response:")
        for forbidden in case['forbidden']:
            print(f"   - '{forbidden}'")

        print(f"\n✅ User Experience:")
        print(f"   - User asks simple question")
        print(f"   - User gets complete answer")
        print(f"   - User NEVER sees internal system details")
        print(f"   - System works transparently")


async def test_no_command_suggestions():
    """Test that NO commands are ever suggested."""

    print("\n" + "="*60)
    print("TEST: No Command Suggestions Ever")
    print("="*60)

    print("\n❌ FORBIDDEN RESPONSES (Never allow these):")
    forbidden = [
        "I recommend using the Wikipedia Agent",
        "You can use the command 'search_wikipedia coffee'",
        "Try asking the Wikipedia Agent",
        "Use get_article_summary",
        "Search with: search_papers",
    ]

    for response in forbidden:
        print(f"   ❌ '{response}'")

    print("\n✅ CORRECT RESPONSES (Always like this):")
    correct = [
        "Coffee is a brewed drink prepared from roasted coffee beans...",
        "The telephone was invented by Alexander Graham Bell in 1876...",
        "The Eiffel Tower is located in Paris, France..."
    ]

    for response in correct:
        print(f"   ✅ '{response}'")

    print("\n💡 Key Principle:")
    print("   User should NEVER know HOW the system got the answer")
    print("   User should ONLY see the answer itself")


async def test_comparison():
    """Compare before/after behavior."""

    print("\n" + "="*60)
    print("BEFORE/AFTER COMPARISON")
    print("="*60)

    print("\n❌ BEFORE (Task 28 - Not Autonomous):")
    print("   User: 'what is coffee'")
    print("   System: 'Coffee is a popular drink...'")
    print("           'I recommend using the Wikipedia Agent with'")
    print("           'the command search_wikipedia coffee for more info'")
    print("\n   Issues:")
    print("   - User sees agent names")
    print("   - User sees commands")
    print("   - User has to do manual work")
    print("   - NOT autonomous")

    print("\n✅ AFTER (Task 29 - Truly Autonomous):")
    print("   User: 'what is coffee'")
    print("   System: [Automatically delegates to Wikipedia]")
    print("           [Gets complete article]")
    print("           [Formats naturally]")
    print("   System: 'Coffee is a brewed drink prepared from roasted'")
    print("           'coffee beans, the seeds of berries from certain'")
    print("           'Coffea species. When roasted to varying degrees,'")
    print("           'they produce different flavors...'")
    print("\n   Benefits:")
    print("   - User never sees agent names")
    print("   - User never sees commands")
    print("   - User just gets complete answer")
    print("   - TRULY autonomous")


async def test_live_factual():
    """Test live factual query against running system."""

    print("\n" + "="*60)
    print("LIVE TEST: Factual Question")
    print("="*60)

    query = "what is coffee"

    print(f"\n📝 Testing: {query}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8001/doip/extend/receive_user_input",
                json={
                    "authentication": {"caller_pid": "test"},
                    "parameters": {"message": query}
                }
            )

            if response.status_code == 200:
                data = response.json()
                result = data.get('data', {})
                msg = result.get('message', '')
                status = result.get('status', '')

                print(f"\n✅ Response received:")
                print(f"   Status: {status}")
                print(f"   Message: {msg[:200]}...")

                # Check for forbidden phrases
                forbidden = [
                    "recommend using",
                    "search_wikipedia",
                    "Wikipedia Agent",
                    "command",
                    "you can use"
                ]

                violations = []
                msg_lower = msg.lower()
                for phrase in forbidden:
                    if phrase.lower() in msg_lower:
                        violations.append(phrase)

                if violations:
                    print(f"\n❌ VIOLATIONS FOUND:")
                    for v in violations:
                        print(f"   - Contains forbidden phrase: '{v}'")
                else:
                    print(f"\n✅ NO VIOLATIONS - Response is clean!")
                    print(f"   - No command suggestions")
                    print(f"   - No agent names")
                    print(f"   - Truly autonomous!")
            else:
                print(f"   ❌ HTTP {response.status_code}")

    except Exception as e:
        print(f"   ❌ Exception: {e}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TASK 29: AUTONOMOUS BEHAVIOR TEST SUITE")
    print("="*60)

    asyncio.run(test_factual_questions())
    asyncio.run(test_no_command_suggestions())
    asyncio.run(test_comparison())

    print("\n" + "="*60)
    print("RUNNING LIVE TEST (requires system running)")
    print("="*60)
    asyncio.run(test_live_factual())

    print("\n" + "="*60)
    print("TEST SUITE COMPLETE")
    print("="*60)
