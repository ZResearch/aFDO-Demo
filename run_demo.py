#!/usr/bin/env python3
"""Run demo scenarios for IJCAI 2026 presentation."""

import asyncio
import httpx
import json
from datetime import datetime

class DemoRunner:
    """Run demonstration scenarios."""

    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.results = []

    async def run_scenario(self, name: str, message: str):
        """Run a single demo scenario."""
        print(f"\n{'='*60}")
        print(f"📋 Scenario: {name}")
        print(f"{'='*60}")
        print(f"User: {message}")
        print("-" * 60)

        start_time = datetime.now()

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/doip/extend/receive_user_input",
                    json={
                        "protocol_version": "2.0",
                        "authentication": {"caller_pid": "demo-runner"},
                        "parameters": {"message": message}
                    }
                )

                result = response.json()

                duration = (datetime.now() - start_time).total_seconds()

                if result.get("status") == "success":
                    data = result.get("data", {})
                    response_text = data.get("response", "No response")

                    print(f"Assistant: {response_text[:500]}...")
                    print(f"\n✅ Success (took {duration:.2f}s)")

                    # Show workflow
                    workflow = data.get("workflow", {})
                    if workflow:
                        steps = workflow.get("steps", [])
                        print(f"Workflow: {len(steps)} steps")

                    self.results.append({
                        "scenario": name,
                        "status": "success",
                        "duration": duration
                    })
                else:
                    print(f"❌ Failed: {result}")
                    self.results.append({
                        "scenario": name,
                        "status": "failed",
                        "duration": duration
                    })

        except Exception as e:
            print(f"❌ Error: {e}")
            self.results.append({
                "scenario": name,
                "status": "error",
                "error": str(e)
            })

    async def run_all(self):
        """Run all demo scenarios."""
        print("\n" + "="*60)
        print("🎬 IJCAI 2026 aFDO Demo - Scenario Runner")
        print("="*60)

        # Scenario 1: Simple query
        await self.run_scenario(
            "Simple Query",
            "Hello! Can you help me understand what you can do?"
        )

        # Scenario 2: Paper analysis request
        await self.run_scenario(
            "Paper Analysis Request",
            "I have a research paper about transformer models. Can you analyze it?"
        )

        # Scenario 3: FAIR compliance
        await self.run_scenario(
            "FAIR Compliance Check",
            "How can I check if my dataset is FAIR compliant?"
        )

        # Summary
        print("\n" + "="*60)
        print("📊 Demo Summary")
        print("="*60)

        total = len(self.results)
        success = len([r for r in self.results if r["status"] == "success"])

        print(f"Total scenarios: {total}")
        print(f"Successful: {success}")
        print(f"Failed: {total - success}")

        if success == total:
            print("\n✅ All scenarios passed!")
        else:
            print("\n⚠️  Some scenarios failed")

        print("")

async def main():
    """Main entry point."""
    runner = DemoRunner()
    await runner.run_all()

if __name__ == "__main__":
    asyncio.run(main())
