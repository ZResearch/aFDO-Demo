# Restart Required for Activity Logs

## Why Restart?

The activity logging code was added to `shared/afdo_base.py`, but the agents are currently running with the old code loaded in memory. They need to be restarted to load the new logging implementation.

## Steps to Restart

### 1. Stop the Current System
```bash
./stop_system.sh
```

Wait a few seconds to ensure all processes are terminated.

### 2. Verify Everything Stopped
```bash
ps aux | grep python | grep -E "(registry|agent|chat_ui)" | grep -v grep
```

If any processes remain, kill them manually:
```bash
pkill -f "registry/main.py"
pkill -f "agents/"
```

### 3. Start the System Fresh
```bash
./start_system.sh
```

This will start all agents with the new activity logging code.

### 4. Wait for Startup
Wait ~10 seconds for all agents to register with the registry.

### 5. Run the Test
```bash
python3 test_activity_logs.py
```

This time, you should see activity logs being populated!

## Expected Output

After restarting and running the test:

```
   Checking Paper Analyzer (21.T11148/afdo-paper-analyzer)...
   📊 Found 3 outgoing calls      ← Should see calls now!
   📊 Found 1 incoming calls      ← Should see calls now!
   ✅ Outgoing calls logged!

   Sample outgoing call:
     - Timestamp: 2026-02-11T15:30:45.123Z
     - Target: 21.T11148/afdo-pdf-parser
     - Operation: extract_text
     - Status: success
     - Duration: 2.34s
     - Cost: $0.0500
```

## Quick Restart Command

```bash
./stop_system.sh && sleep 3 && ./start_system.sh && sleep 10 && python3 test_activity_logs.py
```

This will:
1. Stop the system
2. Wait 3 seconds
3. Start the system
4. Wait 10 seconds for registration
5. Run the test automatically

## Troubleshooting

### Test still shows empty logs

**Check if agents restarted:**
```bash
ps aux | grep "afdo_base.py" | grep -v grep
```

The processes should have recent start times.

**Check if new code is loaded:**
```bash
# Look for recent logs showing the new logging behavior
tail -f logs/registry.log
```

### Agents won't start

**Check for port conflicts:**
```bash
lsof -i :8000  # Registry
lsof -i :8001  # NL Handler
lsof -i :8003  # Paper Analyzer
lsof -i :8004  # PDF Parser
```

**Check logs for errors:**
```bash
./view_logs.sh
```

## Why This Happens

Python loads code into memory when a process starts. The agents are long-running processes, so they don't automatically pick up code changes. This is normal behavior - any time you modify agent code, you need to restart the agents for changes to take effect.

## Alternative: Restart Individual Agents

If you only want to restart specific agents:

```bash
# Find and kill specific agent
pkill -f "paper_analyzer_agent.py"

# Restart just that agent
python3 agents/paper_analyzer/paper_analyzer_agent.py &
```

But it's usually easier to restart the whole system.
