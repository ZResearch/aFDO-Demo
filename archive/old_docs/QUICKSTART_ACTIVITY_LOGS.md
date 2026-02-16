# Quick Start: Activity Logs

## What Was Implemented

Activity logs now automatically track all agent interactions and persist them to FDO records in the registry.

## Quick Test

### 1. Start the System
```bash
./start_system.sh
```

Wait for all agents to start (Registry, NL Handler, Paper Analyzer, PDF Parser, FAIR Assessor).

### 2. Run the Test
```bash
python3 test_activity_logs.py
```

This will:
- Make a test request that triggers agent interactions
- Wait for logs to sync (6 seconds)
- Verify activity logs are working
- Show sample log entries

### 3. Or Use Quick Verification
```bash
./verify_activity_logs.sh
```

## What to Expect

After running the test, you should see:

```
✅ ACTIVITY LOGS TEST PASSED!

Key findings:
  ✓ Activity log field exists in FDO records
  ✓ Activity log has correct structure (calls_made/calls_received)
  ✓ Outgoing calls are being logged automatically
  ✓ Incoming calls are being logged automatically
  ✓ Logs are persisted to registry FDO records
  ✓ All required fields are present in log entries
```

## Manual Inspection

To see the activity logs directly:

```bash
# View Paper Analyzer's activity log
cat registry/data/fdos/21.T11148-afdo-paper-analyzer.json | jq '.activity_log'

# View PDF Parser's activity log
cat registry/data/fdos/21.T11148-afdo-pdf-parser.json | jq '.activity_log'

# View NL Handler's activity log
cat registry/data/fdos/21.T11148-afdo-nl-handler-scientific.json | jq '.activity_log'
```

## Activity Log Structure

Each FDO now has:

```json
{
  "activity_log": {
    "calls_made": [
      {
        "timestamp": "2026-02-11T15:30:45.123Z",
        "target_pid": "21.T11148/afdo-pdf-parser",
        "operation": "extract_text",
        "status": "success",
        "duration": 2.34,
        "cost": 0.05
      }
    ],
    "calls_received": [
      {
        "timestamp": "2026-02-11T15:30:42.789Z",
        "caller_pid": "21.T11148/afdo-nl-handler",
        "operation": "analyze_paper",
        "status": "success",
        "duration": 15.67
      }
    ]
  }
}
```

## Troubleshooting

### Logs are empty
- Wait at least 6 seconds after making a request (logs batch every 5 seconds)
- Check that agents are running: `./check_status.sh`

### Test fails with connection errors
- Ensure all agents are running on their expected ports
- Check logs: `./view_logs.sh`

### Registry endpoint not found
- Restart the registry after the implementation changes
- Verify the PATCH endpoint exists: `curl http://localhost:8000/openapi.json | jq '.paths | keys'`

## Key Features

✅ **Automatic**: Every call is logged without manual intervention
✅ **Bidirectional**: Both outgoing and incoming calls tracked
✅ **Bounded**: Limited to 100 entries (prevents unbounded growth)
✅ **Persistent**: Synced to registry every 5 seconds
✅ **Complete**: Includes timestamps, duration, cost, status

## Next Steps

1. Run the system with `./start_system.sh`
2. Run the test with `python3 test_activity_logs.py`
3. Verify results with `./verify_activity_logs.sh`
4. View actual logs in FDO records
5. Update AUDIT_FINDINGS.md to mark Issue #3 as resolved

## Documentation

- **ACTIVITY_LOGS_IMPLEMENTATION.md** - Complete implementation details
- **AUDIT_FINDINGS.md** - Original audit that identified this issue
- **test_activity_logs.py** - Automated test script
- **verify_activity_logs.sh** - Quick verification script
