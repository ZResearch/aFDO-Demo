# Centralized Logging System

## Overview

The aFDO system now has a comprehensive centralized logging system that logs all activities to a single file with detailed information. The log file is automatically reinitialized (cleared) when any service restarts.

## Log Location

**Log File**: `/home/boukhers/IJCAI_DEMO/logs/system.log`

All agents (Registry, Chat UI, NL Handler, Paper Analyzer, PDF Parser, FAIR Assessor, LLM endpoints) log to this single file.

## Log Format

```
[timestamp] [level] [agent_name] message
```

Example:
```
[2026-02-09 16:16:03] [INFO    ] [Chat UI] 📝 REGISTERED | PID: 21.T11148/afdo-chat-ui | Port: 8001 | Operations: receive_user_input, display_message
[2026-02-09 16:16:15] [INFO    ] [Chat UI] 🔵 START receive_user_input | Caller: web-user | Params: {message=Analyze this paper...}
[2026-02-09 16:16:18] [INFO    ] [Chat UI] ✅ SUCCESS receive_user_input | Duration: 2.845s | Result: status=success
```

## Log Levels

- **DEBUG**: Detailed diagnostic information (heartbeats, budget transactions, etc.)
- **INFO**: General informational messages (operations, calls, registrations)
- **WARNING**: Warning messages (failed attempts, alternative provider selection)
- **ERROR**: Error messages (operation failures, connection errors)
- **CRITICAL**: Critical system failures

## Logged Events

### Startup & Shutdown
- **Agent Startup**: When any agent starts
  ```
  [INFO] [Chat UI] 🚀 STARTUP | Version: 2.0.0 | Config: port=8001, operations=4
  ```

- **Agent Shutdown**: When any agent shuts down
  ```
  [INFO] [PDF Parser] 🛑 SHUTDOWN | Reason: normal
  ```

### Registration
- **Agent Registration**: When an agent registers with the registry
  ```
  [INFO] [Registry] 📝 REGISTERED | PID: 21.T11148/afdo-pdf-parser | Port: 8002 | Operations: extract_text
  ```

### Operations
- **Operation Start**: When an agent receives a request
  ```
  [INFO] [Paper Analyzer] 🔵 START analyze_paper_budget | Caller: 21.T11148/afdo-chat-ui | Params: {pdf_data=bytes[...], budget=1.00}
  ```

- **Operation Success**: When an operation completes successfully
  ```
  [INFO] [Paper Analyzer] ✅ SUCCESS analyze_paper_budget | Duration: 3.456s | Result: status=success
  ```

- **Operation Error**: When an operation fails
  ```
  [ERROR] [PDF Parser] ❌ ERROR extract_text | Error: Failed to parse PDF | Duration: 0.234s
  ```

### Inter-Agent Communication
- **Agent Calls**: When one agent calls another
  ```
  [INFO] [Paper Analyzer] 📤 CALL Paper Analyzer → PDF Parser.extract_text
  [INFO] [Paper Analyzer] ✅ RESPONSE from PDF Parser | Duration: 1.234s
  ```

### Budget Management
- **Budget Transactions**: Reserve, commit, and release operations
  ```
  [DEBUG] [Paper Analyzer] 💰 BUDGET RESERVE | Amount: $0.0500 | Remaining: $0.9500
  [DEBUG] [Paper Analyzer] 💰 BUDGET COMMIT | Amount: $0.0480 | Remaining: $0.9520
  [DEBUG] [Paper Analyzer] 💰 BUDGET RELEASE | Amount: $0.0500 | Remaining: $1.0000
  ```

### Heartbeats
- **Heartbeat Events**: Periodic status updates (debug level)
  ```
  [DEBUG] [PDF Parser] 💓 HEARTBEAT | Status: available, queue=0
  ```

- **Registry Heartbeat Reception**: When registry receives heartbeats (debug level)
  ```
  [DEBUG] [Registry] 💓 Heartbeat from PDF Parser (queue=0, load=0.00)
  ```

### Reputation
- **Reputation Updates**: When an agent's reputation changes
  ```
  [INFO] [PDF Parser] ⭐ REPUTATION 0.85 → 0.87 (+0.02) | successful operation
  ```

### Queue Management
- **Queue Events**: Queue additions, processing (debug level)
  ```
  [DEBUG] [PDF Parser] 📊 QUEUE ADD | Position: 0, Priority: normal
  [DEBUG] [PDF Parser] 📊 QUEUE PROCESS | Completed request from position 0
  ```

### Failures & Recovery
- **Failure Reports**: When operations fail
  ```
  [ERROR] [Registry] Failure reported: 21.T11148/afdo-pdf-parser.extract_text() by 21.T11148/afdo-chat-ui - Connection timeout
  ```

- **Alternative Provider Selection**: When retrying with alternatives
  ```
  [WARNING] [Paper Analyzer] Attempt 1 failed: Connection timeout
  [INFO] [Paper Analyzer] Trying alternative provider...
  [INFO] [Paper Analyzer] Selected provider 21.T11148/afdo-pdf-parser-2 for extract_text (cost: $0.0500)
  ```

### Registry Operations
- **FDO Registration**: When agents register
  ```
  [INFO] [Registry] Registering FDO: 21.T11148/afdo-pdf-parser (PDF Parser) on port 8002
  ```

- **Cleanup Operations**: When inactive agents are marked or deleted
  ```
  [WARNING] [Registry] Marked 21.T11148/afdo-old-agent as inactive (no heartbeat for 120s)
  [INFO] [Registry] Deleted FDO 21.T11148/afdo-old-agent (inactive for 24.5 hours)
  ```

## Viewing Logs

### View entire log
```bash
cat logs/system.log
```

### View recent logs
```bash
tail -f logs/system.log
```

### View logs for specific agent
```bash
grep "Chat UI" logs/system.log
```

### View only errors
```bash
grep "ERROR" logs/system.log
```

### View operation flows
```bash
grep "START\|SUCCESS\|ERROR" logs/system.log
```

### View budget transactions
```bash
grep "BUDGET" logs/system.log
```

### View inter-agent calls
```bash
grep "CALL\|RESPONSE" logs/system.log
```

## Log Rotation & Reinitialization

**Important**: The log file is automatically **cleared and reinitialized** when:
- The registry starts
- Any agent starts (via the shared logger singleton)

This ensures you always have fresh logs for the current session.

If you want to preserve previous logs, manually copy them before restarting:
```bash
cp logs/system.log logs/system-backup-$(date +%Y%m%d-%H%M%S).log
```

## Using the Logger in Code

### Basic Usage

```python
from shared.logging_config import get_logger

logger = get_logger()

# Basic logging
logger.info("My Agent", "Operation completed successfully")
logger.error("My Agent", "Connection failed")
logger.warning("My Agent", "Using fallback provider")
logger.debug("My Agent", "Processing item 3 of 10")
```

### Structured Logging

```python
# Operation lifecycle
logger.operation_start("My Agent", "process_data", "caller-pid", {"input": "data"})
logger.operation_success("My Agent", "process_data", duration=1.5, result_summary="processed 100 items")
logger.operation_error("My Agent", "process_data", "Timeout error", duration=30.0)

# Agent communication
logger.agent_call("My Agent", "Target Agent", "operation_name", cost=0.05)
logger.agent_response("My Agent", "Caller Agent", success=True, duration=2.3)

# Budget tracking
logger.budget_transaction("My Agent", "RESERVE", amount=0.10, remaining=0.90)
logger.budget_transaction("My Agent", "COMMIT", amount=0.08, remaining=0.92)
logger.budget_transaction("My Agent", "RELEASE", amount=0.10, remaining=1.00)

# Startup/shutdown
logger.startup("My Agent", version="1.0.0", config={"port": 8000, "type": "worker"})
logger.shutdown("My Agent", reason="user requested")

# Registration
logger.registration("My Agent", pid="21.T11148/my-agent", port=8000, operations=["op1", "op2"])

# Heartbeat
logger.heartbeat("My Agent", status="active, queue=2")

# Reputation
logger.reputation_update("My Agent", old_score=0.85, new_score=0.87, reason="successful operation")

# Queue management
logger.queue_event("My Agent", "ADD", details="position=0, priority=high")
```

## Performance Considerations

- **Console Output**: Only INFO level and above (to avoid console spam)
- **File Output**: ALL levels including DEBUG (for comprehensive diagnostics)
- **Heartbeats**: Logged at DEBUG level to avoid cluttering INFO logs
- **Budget Transactions**: Logged at DEBUG level for detailed tracking
- **Non-blocking**: Logging is synchronous but fast (minimal performance impact)

## Debugging Workflows

### Example: Tracing a Paper Analysis Request

1. **Start monitoring**:
   ```bash
   tail -f logs/system.log
   ```

2. **Submit request through Chat UI**

3. **Watch the flow**:
   ```
   [INFO] [Chat UI] 🔵 START receive_user_input | Caller: web-user
   [INFO] [Chat UI] Selected provider Paper Analyzer for analyze_paper_budget
   [DEBUG] [Chat UI] 💰 BUDGET RESERVE | Amount: $0.5000 | Remaining: $0.5000
   [INFO] [Chat UI] 📤 CALL Chat UI → Paper Analyzer.analyze_paper_budget
   [INFO] [Paper Analyzer] 🔵 START analyze_paper_budget | Caller: chat-ui
   [INFO] [Paper Analyzer] Selected provider PDF Parser for extract_text
   [DEBUG] [Paper Analyzer] 💰 BUDGET RESERVE | Amount: $0.0500
   [INFO] [Paper Analyzer] 📤 CALL Paper Analyzer → PDF Parser.extract_text
   [INFO] [PDF Parser] 🔵 START extract_text | Caller: paper-analyzer
   [INFO] [PDF Parser] ✅ SUCCESS extract_text | Duration: 1.234s
   [INFO] [Paper Analyzer] ✅ RESPONSE from PDF Parser | Duration: 1.234s
   [DEBUG] [Paper Analyzer] 💰 BUDGET COMMIT | Amount: $0.0480
   ... (continues for LLM calls, FAIR assessment) ...
   [INFO] [Paper Analyzer] ✅ SUCCESS analyze_paper_budget | Duration: 5.678s
   [INFO] [Chat UI] ✅ SUCCESS receive_user_input | Duration: 5.678s
   ```

### Example: Debugging a Failure

```bash
# Find all errors
grep "ERROR" logs/system.log

# Trace a specific operation
grep "extract_text" logs/system.log

# See retry attempts
grep "Attempt\|alternative" logs/system.log
```

## Integration with Existing Agents

The logging system is already integrated into:
- ✅ **shared/afdo_base.py** - Base class for all agents
- ✅ **registry/main.py** - Registry operations
- ✅ All agents automatically inherit logging from base class

All existing agents now log automatically through the base class methods.

## Customization

To adjust log verbosity, edit `/home/boukhers/IJCAI_DEMO/shared/logging_config.py`:

```python
# Change file handler level (currently DEBUG)
file_handler.setLevel(logging.DEBUG)  # Change to INFO, WARNING, etc.

# Change console handler level (currently INFO)
console_handler.setLevel(logging.INFO)  # Change to WARNING, ERROR, etc.
```

## Troubleshooting

### Log file not updating
- Check file permissions on `logs/system.log`
- Ensure `logs/` directory exists (created automatically)
- Restart all services to reinitialize logging

### Too much output
- Set console handler to WARNING or ERROR level
- Use `grep` to filter relevant logs
- Heartbeats are at DEBUG level, won't show in console

### Want to keep history
- Manually backup logs before restarting:
  ```bash
  cp logs/system.log logs/archive/system-$(date +%Y%m%d-%H%M%S).log
  ```

## Summary

The centralized logging system provides:
- ✅ **Single log file** for entire system
- ✅ **Automatic reinitialization** on service restart
- ✅ **Structured, searchable logs** with consistent format
- ✅ **Detailed operation tracking** (start, success, error)
- ✅ **Budget and cost tracking**
- ✅ **Inter-agent communication logs**
- ✅ **Reputation and performance metrics**
- ✅ **Easy debugging** with grep/tail
- ✅ **Minimal performance overhead**

All agents now automatically log their activities through the base class, providing complete observability of the entire aFDO marketplace system.
