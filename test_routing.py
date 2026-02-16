#!/usr/bin/env python3
"""
Test script to evaluate autonomous routing decisions.

Runs test queries through the system and checks if the correct agent was selected.
"""

import json
import httpx
import asyncio
from typing import Dict, List, Any
from datetime import datetime


class RoutingTester:
    def __init__(self, queries_file: str = "test_queries.json"):
        self.queries_file = queries_file
        self.chat_ui_url = "http://localhost:8001"
        self.results = []

    async def load_queries(self) -> List[Dict[str, Any]]:
        """Load test queries from JSON file."""
        with open(self.queries_file, 'r') as f:
            data = json.load(f)
        return data['test_queries']

    async def call_chat_ui(self, query: str) -> Dict[str, Any]:
        """Send query to Chat UI and get response with trace."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.chat_ui_url}/doip/extend/receive_user_input",
                json={
                    "caller_pid": "test-routing-script",
                    "operation": "receive_user_input",
                    "parameters": {"message": query}
                }
            )
            response.raise_for_status()
            return response.json()

    def extract_agent_from_trace(self, result: Dict[str, Any]) -> str:
        """Extract which agent was selected in step2 from the trace."""
        trace = result.get('_trace', {})
        trace_file = trace.get('trace_file', '')

        if not trace_file:
            return "Unknown"

        # Read the trace file
        try:
            with open(trace_file, 'r') as f:
                trace_data = json.load(f)

            # Find step5 (step2 execution) in Chat UI
            events = trace_data.get('events', [])
            for event in events:
                if event.get('step_number') == 5:  # Step 5 is usually step2_find_executor
                    delegated_to = event.get('delegated_to', '')
                    return delegated_to

            return "Unknown"
        except Exception as e:
            print(f"   ⚠️  Could not read trace: {e}")
            return "Unknown"

    async def run_single_test(self, test: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test query."""
        print(f"\n[{test['id']}] Testing: {test['query'][:80]}...")

        try:
            result = await self.call_chat_ui(test['query'])
            actual_agent = self.extract_agent_from_trace(result)
            expected_agent = test['expected_agent']

            # Normalize agent names (handle "Agent" suffix)
            actual_normalized = actual_agent.replace(' Agent', '')
            expected_normalized = expected_agent.replace(' Agent', '')

            match = actual_normalized == expected_normalized or actual_agent == expected_agent

            test_result = {
                'id': test['id'],
                'query': test['query'],
                'category': test['category'],
                'expected_agent': expected_agent,
                'actual_agent': actual_agent,
                'match': match,
                'reason': test['reason'],
                'status': 'success'
            }

            status_icon = "✓" if match else "✗"
            print(f"   {status_icon} Expected: {expected_agent} | Got: {actual_agent}")

            return test_result

        except Exception as e:
            print(f"   ✗ ERROR: {e}")
            return {
                'id': test['id'],
                'query': test['query'],
                'category': test['category'],
                'expected_agent': test['expected_agent'],
                'actual_agent': 'ERROR',
                'match': False,
                'reason': test['reason'],
                'status': 'error',
                'error': str(e)
            }

    async def run_all_tests(self):
        """Run all test queries."""
        print("=" * 80)
        print("ROUTING TEST SUITE")
        print("=" * 80)

        queries = await self.load_queries()
        print(f"\nLoaded {len(queries)} test queries")

        for test in queries:
            result = await self.run_single_test(test)
            self.results.append(result)
            await asyncio.sleep(0.5)  # Brief pause between requests

    def generate_report(self) -> str:
        """Generate a detailed report of test results."""
        report = []
        report.append("\n" + "=" * 80)
        report.append("ROUTING TEST REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)

        # Summary statistics
        total = len(self.results)
        matches = sum(1 for r in self.results if r['match'])
        errors = sum(1 for r in self.results if r['status'] == 'error')
        success_rate = (matches / total * 100) if total > 0 else 0

        report.append(f"\n📊 SUMMARY")
        report.append(f"   Total tests: {total}")
        report.append(f"   Correct routes: {matches} ({success_rate:.1f}%)")
        report.append(f"   Incorrect routes: {total - matches - errors}")
        report.append(f"   Errors: {errors}")

        # Category breakdown
        report.append(f"\n📋 BY CATEGORY")
        categories = {}
        for r in self.results:
            cat = r['category']
            if cat not in categories:
                categories[cat] = {'total': 0, 'correct': 0}
            categories[cat]['total'] += 1
            if r['match']:
                categories[cat]['correct'] += 1

        for cat, stats in sorted(categories.items()):
            rate = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
            report.append(f"   {cat}: {stats['correct']}/{stats['total']} ({rate:.0f}%)")

        # Detailed results
        report.append(f"\n📝 DETAILED RESULTS")
        report.append("")

        for r in self.results:
            status = "✓" if r['match'] else "✗"
            report.append(f"[{r['id']}] {status} {r['category']}")
            report.append(f"   Query: {r['query'][:100]}")
            report.append(f"   Expected: {r['expected_agent']}")
            report.append(f"   Actual: {r['actual_agent']}")
            if not r['match']:
                report.append(f"   Reason: {r['reason']}")
            if r['status'] == 'error':
                report.append(f"   Error: {r.get('error', 'Unknown error')}")
            report.append("")

        # Recommendations
        report.append("💡 RECOMMENDATIONS")
        incorrect = [r for r in self.results if not r['match'] and r['status'] == 'success']

        if not incorrect:
            report.append("   All routes are correct! System is performing optimally.")
        else:
            # Group by expected agent
            by_expected = {}
            for r in incorrect:
                exp = r['expected_agent']
                if exp not in by_expected:
                    by_expected[exp] = []
                by_expected[exp].append(r)

            for agent, cases in by_expected.items():
                report.append(f"   • {agent} description needs improvement:")
                report.append(f"     {len(cases)} queries incorrectly routed to other agents")
                report.append(f"     Categories affected: {', '.join(set(c['category'] for c in cases))}")

        report.append("\n" + "=" * 80)

        return "\n".join(report)

    def save_results(self, filename: str = "test_routing_results.json"):
        """Save detailed results to JSON file."""
        output = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(self.results),
            'correct_routes': sum(1 for r in self.results if r['match']),
            'results': self.results
        }

        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n📄 Detailed results saved to: {filename}")


async def main():
    tester = RoutingTester()
    await tester.run_all_tests()

    report = tester.generate_report()
    print(report)

    tester.save_results()


if __name__ == "__main__":
    asyncio.run(main())
