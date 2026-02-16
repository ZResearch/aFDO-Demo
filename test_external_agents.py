#!/usr/bin/env python3
"""Test external data source agents (Wikipedia, ArXiv, Open Library)."""

import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))


async def test_wikipedia_agent():
    """Test Wikipedia agent functionality."""
    print("\n" + "="*60)
    print("TEST: Wikipedia Agent")
    print("="*60)

    try:
        from agents.wikipedia_agent.wikipedia_agent import WikipediaAgent

        print("\n--- Creating Wikipedia Agent ---")
        agent = WikipediaAgent()
        print(f"✅ Agent created: {agent.name}")
        print(f"   PID: {agent.pid}")
        print(f"   Operations: {agent.operations}")

        # Load policy
        print("\n--- Loading Policy ---")
        agent.policy_engine = agent._load_policy_engine()
        if agent.policy_engine:
            policy_info = agent.policy_engine.get_policy_info()
            print(f"✅ Policy loaded: {policy_info['policy_id']}")
            print(f"   Rules: {policy_info['rule_count']}")
        else:
            print("⚠️  No policy loaded")

        # Test 1: Get article summary
        print("\n--- Test 1: Get Article Summary ---")
        result = await agent.handle_operation(
            operation="get_article_summary",
            caller_pid="test",
            parameters={"topic": "Python (programming language)"}
        )
        print(f"✅ Title: {result.get('title')}")
        print(f"   Summary length: {len(result.get('summary', ''))} chars")
        print(f"   URL: {result.get('url', '')}")

        # Test 2: Search Wikipedia
        print("\n--- Test 2: Search Wikipedia ---")
        result = await agent.handle_operation(
            operation="search_wikipedia",
            caller_pid="test",
            parameters={"query": "artificial intelligence", "limit": 3}
        )
        print(f"✅ Found {result.get('count', 0)} results")
        for i, r in enumerate(result.get('results', [])[:3], 1):
            print(f"   {i}. {r.get('title')}")

        print("\n✅ Wikipedia Agent tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Wikipedia Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_arxiv_agent():
    """Test ArXiv agent functionality."""
    print("\n" + "="*60)
    print("TEST: ArXiv Agent")
    print("="*60)

    try:
        from agents.arxiv_agent.arxiv_agent import ArxivAgent

        print("\n--- Creating ArXiv Agent ---")
        agent = ArxivAgent()
        print(f"✅ Agent created: {agent.name}")
        print(f"   PID: {agent.pid}")
        print(f"   Operations: {agent.operations}")

        # Load policy
        print("\n--- Loading Policy ---")
        agent.policy_engine = agent._load_policy_engine()
        if agent.policy_engine:
            policy_info = agent.policy_engine.get_policy_info()
            print(f"✅ Policy loaded: {policy_info['policy_id']}")
            print(f"   Rules: {policy_info['rule_count']}")
        else:
            print("⚠️  No policy loaded")

        # Test: Search papers
        print("\n--- Test: Search Papers ---")
        result = await agent.handle_operation(
            operation="search_papers",
            caller_pid="test",
            parameters={"query": "machine learning", "max_results": 3}
        )
        print(f"✅ Found {result.get('count', 0)} papers")
        for i, paper in enumerate(result.get('papers', [])[:3], 1):
            print(f"   {i}. {paper.get('title')[:60]}...")
            print(f"      Authors: {', '.join(paper.get('authors', [])[:2])}")

        print("\n✅ ArXiv Agent tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ ArXiv Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_openlibrary_agent():
    """Test Open Library agent functionality."""
    print("\n" + "="*60)
    print("TEST: Open Library Agent")
    print("="*60)

    try:
        from agents.openlibrary_agent.openlibrary_agent import OpenLibraryAgent

        print("\n--- Creating Open Library Agent ---")
        agent = OpenLibraryAgent()
        print(f"✅ Agent created: {agent.name}")
        print(f"   PID: {agent.pid}")
        print(f"   Operations: {agent.operations}")

        # Load policy
        print("\n--- Loading Policy ---")
        agent.policy_engine = agent._load_policy_engine()
        if agent.policy_engine:
            policy_info = agent.policy_engine.get_policy_info()
            print(f"✅ Policy loaded: {policy_info['policy_id']}")
            print(f"   Rules: {policy_info['rule_count']}")
        else:
            print("⚠️  No policy loaded")

        # Test: Search books
        print("\n--- Test: Search Books ---")
        result = await agent.handle_operation(
            operation="search_books",
            caller_pid="test",
            parameters={"query": "python programming", "limit": 3}
        )
        print(f"✅ Found {result.get('count', 0)} books")
        for i, book in enumerate(result.get('books', [])[:3], 1):
            print(f"   {i}. {book.get('title')}")
            authors = book.get('authors', [])
            if authors:
                print(f"      By: {', '.join(authors[:2])}")

        print("\n✅ Open Library Agent tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Open Library Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_policy_decisions():
    """Test that policies make correct decisions."""
    print("\n" + "="*60)
    print("TEST: Policy-Based Decisions")
    print("="*60)

    try:
        from agents.wikipedia_agent.wikipedia_agent import WikipediaAgent

        agent = WikipediaAgent()
        agent.policy_engine = agent._load_policy_engine()

        if not agent.policy_engine:
            print("⚠️  Skipping - no policy engine")
            return True

        # Test 1: Simple operation (should handle alone)
        print("\n--- Test 1: Simple operation (handle alone) ---")
        decision = await agent.policy_engine.decide(
            operation="get_article_summary",
            parameters={"topic": "test"},
            context={}
        )
        print(f"Decision: {decision.decision.value}")
        print(f"Reasoning: {decision.reasoning}")
        assert decision.decision.value == "handle_alone"
        print("✅ Correct decision")

        # Test 2: Complex operation (should query planner)
        print("\n--- Test 2: Complex operation (query planner) ---")
        decision = await agent.policy_engine.decide(
            operation="research_topic",
            parameters={"p1": "v1", "p2": "v2", "p3": "v3",
                       "p4": "v4", "p5": "v5"},  # 5 params = complex
            context={}
        )
        print(f"Decision: {decision.decision.value}")
        print(f"Reasoning: {decision.reasoning}")
        print(f"Complexity assessed: complex (5 parameters)")
        assert decision.decision.value == "query_registry_for_planner"
        print("✅ Correct decision")

        # Test 3: Unknown operation (should find helper)
        print("\n--- Test 3: Unknown operation (find helper) ---")
        decision = await agent.policy_engine.decide(
            operation="unknown_operation",
            parameters={"param": "value"},
            context={}
        )
        print(f"Decision: {decision.decision.value}")
        print(f"Reasoning: {decision.reasoning}")
        assert decision.decision.value == "query_registry_for_helper"
        print("✅ Correct decision")

        print("\n✅ Policy decision tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Policy decision test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all external agent tests."""
    print("\n" + "="*60)
    print("EXTERNAL AGENTS TEST SUITE")
    print("="*60)

    all_passed = True

    if not await test_wikipedia_agent():
        all_passed = False

    if not await test_arxiv_agent():
        all_passed = False

    if not await test_openlibrary_agent():
        all_passed = False

    if not await test_policy_decisions():
        all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL EXTERNAL AGENT TESTS PASSED!")
        print("="*60 + "\n")
        return True
    else:
        print("❌ SOME EXTERNAL AGENT TESTS FAILED!")
        print("="*60 + "\n")
        return False


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
