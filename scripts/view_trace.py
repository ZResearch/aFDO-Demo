"""
View execution trace in readable format.

Usage:
    python scripts/view_trace.py <trace_file.json>
    python scripts/view_trace.py --latest
"""

import sys
import json
from pathlib import Path
from datetime import datetime


def view_trace(filepath: str):
    """Display trace in readable format."""

    with open(filepath) as f:
        trace = json.load(f)

    summary = trace["summary"]
    events = trace["events"]

    print("="*80)
    print(f"EXECUTION TRACE: {summary['request_id']}")
    print("="*80)

    print(f"\nUser Query: {summary.get('user_query', 'N/A')}")
    print(f"Duration: {summary['total_duration_ms']}ms")
    print(f"Cost: ${summary['total_cost']:.4f}")
    print(f"Status: {summary['status']}")
    print(f"Agents: {', '.join(summary['agents_involved'])}")

    print("\n" + "="*80)
    print("EXECUTION FLOW")
    print("="*80)

    for event in events:
        print(f"\n[{event['step_number']}] {event['agent_name']} → {event['action_type'].upper()}")
        print(f"    Operation: {event['operation']}")

        if event.get('policy_rule'):
            print(f"    Policy: {event['policy_rule']}")
            print(f"    Reasoning: {event['policy_reasoning']}")

        if event.get('delegated_to'):
            print(f"    Delegated to: {event['delegated_to']}")

        if event.get('duration_ms'):
            print(f"    Duration: {event['duration_ms']}ms")

        if event.get('cost'):
            print(f"    Cost: ${event['cost']:.4f}")

        if event.get('input_data') and event['action_type'] in ["receive", "delegate", "prepare_input"]:
            input_preview = str(event['input_data'])[:150]
            print(f"    Input: {input_preview}...")

        if event.get('output_data') and event['action_type'] in ["select", "receive_result"]:
            output_preview = str(event['output_data'])[:150]
            print(f"    Output: {output_preview}...")

        if event.get('notes'):
            print(f"    Notes: {event['notes']}")

        if event.get('error'):
            print(f"    ❌ ERROR: {event['error']}")

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total Steps: {summary['total_steps']}")
    print(f"Total Duration: {summary['total_duration_ms']}ms")
    print(f"Total Cost: ${summary['total_cost']:.4f}")
    print(f"Status: {summary['status']}")
    print("="*80)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--latest":
            # Find latest trace
            trace_dir = Path("/tmp/afdo_traces")
            if not trace_dir.exists():
                print("No trace directory found at /tmp/afdo_traces")
                sys.exit(1)

            traces = sorted(trace_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            if traces:
                print(f"Viewing latest trace: {traces[0].name}\n")
                view_trace(str(traces[0]))
            else:
                print("No traces found in /tmp/afdo_traces")
        else:
            view_trace(sys.argv[1])
    else:
        print("Usage: python view_trace.py <file> or --latest")
        print("\nExample:")
        print("  python scripts/view_trace.py --latest")
        print("  python scripts/view_trace.py /tmp/afdo_traces/req_abc123_20260212.json")
