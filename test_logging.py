#!/usr/bin/env python3
"""Quick test script to verify logging system."""

import sys
from pathlib import Path

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent))

from shared.logging_config import get_logger

def test_logging():
    """Test all logging functions."""
    logger = get_logger()

    print("Testing centralized logging system...\n")

    # Test basic logging
    logger.info("Test Agent", "This is an info message")
    logger.debug("Test Agent", "This is a debug message")
    logger.warning("Test Agent", "This is a warning message")
    logger.error("Test Agent", "This is an error message")

    # Test structured logging
    logger.startup("Test Agent", version="1.0.0", config={"port": 8000, "type": "test"})

    logger.operation_start(
        "Test Agent",
        "test_operation",
        "caller-123",
        {"param1": "value1", "param2": "value2"}
    )

    logger.operation_success("Test Agent", "test_operation", 1.234, "result=success")

    logger.agent_call("Test Agent", "Target Agent", "do_something", cost=0.05)

    logger.budget_transaction("Test Agent", "RESERVE", 0.10, 0.90)
    logger.budget_transaction("Test Agent", "COMMIT", 0.08, 0.92)

    logger.registration("Test Agent", "21.T11148/afdo-test", 8000, ["op1", "op2"])

    logger.heartbeat("Test Agent", status="active, queue=2")

    logger.reputation_update("Test Agent", 0.85, 0.87, reason="successful operation")

    logger.shutdown("Test Agent", reason="test complete")

    print("\n✅ All logging tests complete!")
    print(f"📝 Check the log file at: logs/system.log")

if __name__ == "__main__":
    test_logging()
