"""Shared utility functions for aFDO demo."""

import uuid
from datetime import datetime
from typing import Dict, Any, List


def generate_pid(prefix: str = "21.T11148", suffix: str = None) -> str:
    """
    Generate a persistent identifier using Handle System format.

    Args:
        prefix: Handle prefix (default: "21.T11148" - recognized Handle prefix)
        suffix: Optional deterministic suffix. If None, generates random UUID.

    Returns:
        A unique PID in format: {prefix}/afdo-{suffix}

    Example:
        >>> pid = generate_pid()
        >>> print(pid)
        21.T11148/afdo-a1b2c3d4
        >>> pid = generate_pid(suffix="chat-ui")
        >>> print(pid)
        21.T11148/afdo-chat-ui
    """
    if suffix:
        unique_id = suffix
    else:
        unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}/afdo-{unique_id}"


def current_timestamp() -> str:
    """
    Get current UTC timestamp in ISO 8601 format.

    Returns:
        ISO 8601 formatted timestamp string with 'Z' suffix for UTC

    Example:
        >>> timestamp = current_timestamp()
        >>> print(timestamp)
        2026-01-12T14:30:45.123456Z
    """
    return datetime.utcnow().isoformat() + "Z"


def log_activity(activity_log: List[Dict[str, Any]], event: Dict[str, Any]) -> None:
    """
    Add an event to the activity log with automatic timestamp.

    This function mutates the activity_log list by appending the event
    with a timestamp added. The timestamp is automatically generated
    if not present in the event dictionary.

    Args:
        activity_log: List of activity events (mutated in place)
        event: Dictionary containing event data. Will have 'timestamp'
               added automatically if not present.

    Example:
        >>> log = []
        >>> log_activity(log, {"action": "created", "agent_id": "123"})
        >>> print(log[0])
        {'action': 'created', 'agent_id': '123', 'timestamp': '2026-01-12T14:30:45.123456Z'}
    """
    if "timestamp" not in event:
        event["timestamp"] = current_timestamp()
    activity_log.append(event)
