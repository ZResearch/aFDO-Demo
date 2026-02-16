# aFDO System - Complete User Guide

**Version:** 2.0.0
**Last Updated:** 2026-02-15
**Status:** Production-ready demonstration system

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Starting the System](#starting-the-system)
6. [Using the System](#using-the-system)
7. [Web Interface](#web-interface)
8. [API Usage](#api-usage)
9. [Agent Discovery](#agent-discovery)
10. [Monitoring and Logs](#monitoring-and-logs)
11. [Troubleshooting](#troubleshooting)
12. [System Administration](#system-administration)
13. [Extending the System](#extending-the-system)

---

## Overview

The **aFDO (Autonomous FAIR Digital Object) System** is a multi-agent marketplace for scientific research paper analysis built on FAIR principles. The system features:

- **13 Autonomous Agents** providing specialized services
- **Policy-driven behavior** with customizable decision-making
- **Budget-aware workflows** with cost tracking (soft enforcement)
- **Semantic discovery** for dynamic service selection
- **Multi-level cascading delegation** - agents can recursively delegate
- **Intelligent synthesis detection** - automatic LLM delegation for complex queries
- **Reputation tracking** for quality assurance
- **Complete execution tracing** for transparency

### Implementation Status

The system is **production-ready** with the following feature status:

**✅ Fully Implemented & Active:**
- Policy-driven agent routing with multi-level delegation
- Semantic discovery by operation
- **Multi-level cascading delegation** (agents can delegate to other agents recursively)
- Automatic synthesis detection (queries requiring comparison/analysis trigger delegation)
- Reputation tracking with complete metrics
- Execution trace capture and nesting
- Cost tracking and budget monitoring
- All 13 agents operational

**⚠️ Partially Implemented:**
- Budget enforcement (tracked but not strictly enforced)

**📋 Implemented But Not Used in Production:**
- Workflow generation (LLM Consultant can generate, not called by default)
- Negotiation protocol (complete implementation, agents use direct calls)
- WorkflowEngine (fully coded, never instantiated)

### System Architecture

```
User/Client
    ↓
Chat UI (8001) ← Main Entry Point
    ↓
Registry (8000) ← Service Discovery
    ↓
[Task Agents]           [Composite Agents]        [External Sources]
├─ PDF Parser (8004)    ├─ Paper Analyzer (8003)  ├─ Wikipedia (8010)
├─ FAIR Assessor (8005) ├─ NL Handler (8002)      ├─ ArXiv (8011)
├─ LLM GPT-4 (8007)     └─ LLM Consultant (8014)  └─ Open Library (8012)
├─ LLM GPT-4-mini (8008)
└─ Creator (8006)
```

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set API key
export OPENAI_API_KEY='your-openai-api-key-here'

# 3. Start the system
./start_system.sh

# 4. Open web interface
open http://localhost:8001/ui

# 5. Try a query
# Upload a PDF and click "Analyze Paper"

# 6. Stop when done
./stop_system.sh
```

---

## Installation

### Requirements

- **Python:** 3.10 or higher
- **OS:** Linux or macOS (tested on Ubuntu 22.04)
- **OpenAI API Key:** Required for LLM-powered agents
- **Disk Space:** 2 GB minimum
- **RAM:** 4 GB recommended

### Dependencies

**Core Framework:**
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
httpx==0.25.0
python-multipart==0.0.6
```

**PDF Processing:**
```
PyPDF2==3.0.1
pdfplumber==0.10.3
reportlab==4.0.7
```

**LLM Integration:**
```
openai==1.12.0
tiktoken==0.5.2
anthropic==0.18.1 (optional)
```

**Testing:**
```
pytest==7.4.3
pytest-asyncio==0.21.1
```

### Installation Steps

```bash
# 1. Clone or download repository
cd IJCAI_DEMO

# 2. Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify installation
python3 -c "import fastapi, openai; print('✓ Installation successful')"
```

---

## Configuration

### Environment Variables

**Required:**
- `OPENAI_API_KEY` - Your OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

**Optional:**
- `OPENAI_API_BASE` - Custom OpenAI endpoint (for Ollama or other providers)
- `LLM_MODEL` - Override default model (default: gpt-4o)
- `LOG_LEVEL` - Logging verbosity (DEBUG, INFO, WARNING, ERROR)

### Configuration Methods

**Method 1: Environment Variable (Session Only)**
```bash
export OPENAI_API_KEY='sk-...'
```

**Method 2: .env File (Recommended)**
```bash
# Create .env file in project root
echo "OPENAI_API_KEY='sk-...'" > .env

# The start_system.sh script automatically loads .env
```

**Method 3: Setup Script**
```bash
./setup_api_key.sh
# Follow the prompts
```

### Verify Configuration

```bash
echo $OPENAI_API_KEY
# Should output your API key
```

---

## Starting the System

### Using Startup Script (Recommended)

```bash
./start_system.sh
```

**What Happens:**
1. Loads `.env` file if present
2. Validates `OPENAI_API_KEY`
3. Creates `logs/` directory
4. Checks port availability
5. Starts Registry (port 8000)
6. Initializes type system
7. Starts all 12 agents in dependency order
8. Verifies registration
9. Reports status

**Expected Output:**
```
==========================================
🚀 Starting aFDO Demo System
==========================================

Checking environment...
  ✅ OPENAI_API_KEY is set
  ✅ All required ports available

Starting FDO Registry (port 8000)...
  ✅ Registry started (PID 12345)

Initializing type system...
  ✅ Types initialized

Starting agents...
  ✅ PDF Parser (8004)
  ✅ FAIR Assessor (8005)
  ✅ Creator (8006)
  ✅ LLM GPT-4 (8007)
  ✅ LLM GPT-4-mini (8008)
  ✅ Wikipedia Agent (8010)
  ✅ ArXiv Agent (8011)
  ✅ Open Library Agent (8012)
  ✅ Paper Analyzer (8003)
  ✅ NL Handler (8002)
  ✅ LLM Consultant (8014)
  ✅ Chat UI (8001)

==========================================
✅ All 13 agents started successfully!
==========================================

🌐 Web Interface: http://localhost:8001/ui
📊 Registry Dashboard: http://localhost:8000/
📝 Logs directory: ./logs/

To stop: ./stop_system.sh
To check status: ./check_status.sh
```

### Startup Time

- **Registry:** ~2 seconds
- **Type Initialization:** ~1 second
- **Each Agent:** ~1-2 seconds
- **Total:** ~20-25 seconds for full system

---

## Using the System

### Web Interface (Recommended for Beginners)

The Chat UI provides a user-friendly web interface at `http://localhost:8001/ui`

**Features:**
- Natural language query input
- PDF file upload
- Budget allocation slider
- Policy selection (Cheapest, Fastest, Balanced)
- Real-time cost estimation
- Detailed results with breakdown
- Execution trace viewer

**Example Workflows:**

1. **Analyze Research Paper:**
   - Click "Upload PDF"
   - Select a research paper PDF
   - Set budget: $1.00
   - Select policy: Balanced
   - Click "Analyze Paper"
   - View results and cost breakdown

2. **Check FAIR Compliance:**
   - Enter metadata in JSON format
   - Click "Check FAIR Compliance"
   - Review scores and suggestions

3. **General Query:**
   - Type: "What is machine learning?"
   - System routes to appropriate agents
   - Aggregates results from multiple sources

### Command Line Usage

**Using cURL:**

```bash
# Analyze a paper
curl -X POST http://localhost:8001/doip/call \
  -H "Content-Type: application/json" \
  -d '{
    "target_pid": "21.T11148/afdo-chat-ui",
    "operation": "receive_user_input",
    "caller_pid": "user",
    "parameters": {
      "message": "Analyze this paper",
      "pdf_data": "'$(base64 -w0 paper.pdf)'",
      "budget": 1.0,
      "policy": "balanced"
    }
  }'
```

**Using Python:**

```python
import httpx
import base64

# Read PDF
with open("paper.pdf", "rb") as f:
    pdf_data = base64.b64encode(f.read()).decode()

# Send request
response = httpx.post(
    "http://localhost:8001/doip/call",
    json={
        "target_pid": "21.T11148/afdo-chat-ui",
        "operation": "receive_user_input",
        "caller_pid": "user",
        "parameters": {
            "message": "Analyze this paper",
            "pdf_data": pdf_data,
            "budget": 1.0,
            "policy": "balanced"
        }
    },
    timeout=120.0
)

result = response.json()
print(result)
```

---

## Web Interface

### Accessing the UI

Open browser to: `http://localhost:8001/ui`

### Interface Components

**1. Query Input Area**
- Text input for natural language queries
- File upload button for PDFs
- Supports drag-and-drop

**2. Budget Controls**
- Budget slider ($0.10 - $5.00)
- Real-time cost estimation
- Remaining budget indicator

**3. Policy Selector**
- **Cheapest:** Minimize cost (may take longer)
- **Fastest:** Minimize time (may cost more)
- **Balanced:** Optimize cost vs. quality (recommended)

**4. Results Display**
- Analysis summary
- Key findings and insights
- FAIR compliance scores
- Cost breakdown by service
- Execution trace

**5. Execution Trace**
- Step-by-step execution log
- Agent interactions
- Timing and cost per step
- Policy decisions and reasoning

### Example Queries

**Paper Analysis:**
```
"Analyze this research paper on deep learning"
[Upload PDF]
Budget: $1.00
Policy: Balanced
```

**FAIR Assessment:**
```
"Check FAIR compliance for this metadata"
Metadata: {
  "title": "Research Dataset",
  "authors": ["Dr. Smith"],
  "license": "CC-BY-4.0"
}
```

**Knowledge Query:**
```
"What is quantum computing and what are its applications?"
Budget: $0.50
Policy: Cheapest
```

---

## API Usage

### Registry API

**Base URL:** `http://localhost:8000`

#### Get Registry Info
```bash
curl http://localhost:8000/
```

**Response:**
```json
{
  "service": "FDO Registry System",
  "pid": "21.T11148/registry-system-001",
  "status": "active",
  "stats": {
    "profiles": 1,
    "types": 7,
    "operations": 45,
    "fdos": 12,
    "metadata": 12
  },
  "uptime_seconds": 3600
}
```

#### List All Agents
```bash
curl http://localhost:8000/doip/search/fdos
```

**Response:**
```json
{
  "status": "success",
  "count": 12,
  "fdos": [
    {
      "pid": "21.T11148/afdo-pdf-parser",
      "name": "PDF Parser",
      "port": 8004,
      "operations": ["extract_text", "extract_metadata", "extract_tables"],
      "status": "active",
      "reputation": 0.87,
      "cost": 0.05
    },
    ...
  ]
}
```

#### Find Agents by Operation
```bash
curl "http://localhost:8000/market/agents/by_operation/extract_text?sort_by=balanced"
```

**Response:**
```json
{
  "status": "success",
  "operation": "extract_text",
  "agents": [
    {
      "pid": "21.T11148/afdo-pdf-parser",
      "name": "PDF Parser",
      "current_cost": 0.05,
      "reputation": 0.87,
      "queue_depth": 0,
      "status": "active"
    }
  ],
  "sorted_by": "balanced"
}
```

#### Get Agent Activity Log
```bash
curl http://localhost:8000/registry/fdos/21.T11148/afdo-pdf-parser/activity_log
```

**Response:**
```json
{
  "pid": "21.T11148/afdo-pdf-parser",
  "total_operations": 42,
  "recent_activity": [
    {
      "timestamp": "2026-02-13T10:30:00Z",
      "operation": "extract_text",
      "caller": "21.T11148/afdo-paper-analyzer",
      "duration": 2.3,
      "cost": 0.05,
      "status": "success"
    }
  ]
}
```

### Agent DOIP Endpoints

**Base Pattern:** `http://localhost:{port}/doip/call`

#### Call PDF Parser
```bash
curl -X POST http://localhost:8004/doip/call \
  -H "Content-Type: application/json" \
  -d '{
    "target_pid": "21.T11148/afdo-pdf-parser",
    "operation": "extract_text",
    "caller_pid": "client",
    "parameters": {
      "pdf_data": "<base64-pdf>"
    }
  }'
```

#### Call FAIR Assessor
```bash
curl -X POST http://localhost:8005/doip/call \
  -H "Content-Type: application/json" \
  -d '{
    "target_pid": "21.T11148/afdo-fair-assessor",
    "operation": "assess_fairness",
    "caller_pid": "client",
    "parameters": {
      "metadata": {
        "pid": "21.T11148/example",
        "title": "Research Paper",
        "authors": ["Jane Smith"],
        "license": "CC-BY-4.0"
      }
    }
  }'
```

---

## Agent Discovery

### How Discovery Works

The system uses **semantic discovery with multi-objective scoring** for intelligent agent selection:

1. **Client sends query:** Natural language or specific operation request
2. **Registry performs semantic matching:** Compares query against agent descriptions and operations using sentence transformers
3. **Multi-objective scoring:** Ranks agents using `score = α·semantic + β·reputation - γ·cost`
4. **Returns ranked candidates:** Sorted by composite score (semantic relevance 60%, quality 30%, cost 10%)
5. **Client delegates:** Calls top-ranked agent with automatic fallback

### Discovery Example

```python
# In agent code
agents = await self.discover_by_operation("extract_text")
# Returns: [
#   {
#     "pid": "21.T11148/afdo-pdf-parser",
#     "cost": 0.05,
#     "reputation": 0.87,
#     "queue_depth": 0
#   }
# ]

# Select best agent using policy
selected = self.selection_policy.select(agents)

# Call selected agent
result = await self.call_other_afdo(
    target_pid=selected["pid"],
    operation="extract_text",
    data={"pdf_data": pdf_data}
)
```

### Multi-Objective Agent Ranking

The registry uses **Algorithm 1** from the aFDO paper to rank agents:

**Scoring Formula:**
```
score = α·s_semantic + β·r_reputation - γ·(c_cost/c_max)

Default weights: α=0.6, β=0.3, γ=0.1
```

**How It Works:**

1. **Semantic Similarity (60%):** How well the agent matches the query
   - Embedding-based comparison using sentence transformers
   - Compares against agent description AND individual operations
   - Takes maximum of agent-level and operation-level similarity

2. **Reputation (30%):** Historical performance quality
   - Based on success rate, accuracy, caller ratings
   - Range: 0.0 (poor) to 1.0 (excellent)
   - New agents start at 0.5

3. **Cost Penalty (10%):** Normalized cost consideration
   - Prefers cheaper agents when quality is similar
   - Normalized by maximum cost to prevent bias
   - Low weight ensures quality isn't sacrificed for pennies

**Example Selection:**

```
Query: "who is the president of Algeria"

Wikipedia Agent:
  semantic=0.427, reputation=0.500, cost=$0.01
  score = 0.6(0.427) + 0.3(0.500) - 0.1(0.20) = 0.386 ✓ Selected

Chat UI Agent:
  semantic=0.256, reputation=0.500, cost=$0.00
  score = 0.6(0.256) + 0.3(0.500) - 0.1(0.00) = 0.304

Winner: Wikipedia (better semantic match)
```

**Benefits:**
- ✅ Relevance-first: Semantic match matters most
- ✅ Quality-aware: Proven agents preferred over untested
- ✅ Cost-conscious: Slight preference for cheaper options
- ✅ Configurable: Weights tunable for different priorities

**Legacy Client-Side Policies:**

For specific use cases, simpler client-side policies are available:

- **Cheapest:** Pure cost minimization (ignores quality)
- **Fastest:** Minimizes queue + execution time
- **Best Reputation:** Pure quality maximization (ignores cost)
- **Value:** Maximizes reputation per dollar

**Note:** Multi-objective scoring at the registry level is recommended for most use cases.

---

## Multi-Level Cascading

### How It Works

The system supports **recursive multi-level delegation** where agents can delegate to other agents, which in turn can delegate further:

```
User → Chat UI → Wikipedia → LLM Consultant → Result
     (Level 1)    (Level 2)     (Level 3)
```

### Automatic Synthesis Detection

Agents automatically detect when queries require synthesis or analysis beyond simple data lookup:

**Synthesis Keywords Detected:**
- compare, versus, analyze, evaluate
- explain, why, how does, what makes
- pros and cons, advantages, disadvantages
- better, worse, best, optimal

**Example:**
```
Query: "Compare Algeria and Morocco"

Flow:
1. Chat UI receives query
2. Discovers Wikipedia (best match for "Algeria")
3. Wikipedia receives query
4. Wikipedia detects "compare" keyword
5. Wikipedia policy: query_requires_synthesis = True
6. Wikipedia triggers SEMANTIC_DISCOVERY
7. Wikipedia discovers LLM Consultant
8. Wikipedia delegates to LLM for synthesis
9. LLM returns comparison
10. Results cascade: LLM → Wikipedia → Chat UI → User
```

### Query Types

**Simple Queries (Single-Level):**
- "Who is the president of Algeria" → Wikipedia handles directly
- "What is coffee" → Wikipedia handles directly
- "Search for quantum papers" → ArXiv handles directly

**Synthesis Queries (Multi-Level):**
- "Compare Algeria and Morocco" → Wikipedia → LLM Consultant
- "Explain the difference between X and Y" → Data Source → LLM
- "Analyze pros and cons of blockchain" → Data Source → LLM

### Benefits

1. **Intelligent Routing:** Agents know when they need help
2. **No Hardcoding:** Delegation decisions are policy-driven
3. **Automatic Fallback:** If LLM delegation fails, agent handles best-effort
4. **Complete Tracing:** Full execution trace shows all delegation levels

---

## Monitoring and Logs

### Log Files

All logs stored in `logs/` directory:

```
logs/
├── afdo_2026-02-13.log      # Centralized activity log
├── registry.log              # Registry output
├── chat-ui.log              # Chat UI
├── paper-analyzer.log       # Paper Analyzer
├── pdf-parser.log           # PDF Parser
├── fair-assessor.log        # FAIR Assessor
├── llm-gpt4.log             # LLM GPT-4
├── llm-gpt4-mini.log        # LLM GPT-4-mini
├── nl-handler.log           # NL Handler
├── creator.log              # Creator
├── wikipedia.log            # Wikipedia Agent
├── arxiv.log                # ArXiv Agent
├── openlibrary.log          # Open Library Agent
└── llm-consultant.log       # LLM Consultant
```

### Viewing Logs

**Centralized log (all agents):**
```bash
tail -f logs/afdo_$(date +%Y-%m-%d).log
```

**Specific agent:**
```bash
tail -f logs/pdf-parser.log
```

**Search for errors:**
```bash
grep -i error logs/*.log
```

**Interactive log viewer:**
```bash
./view_logs.sh
```

### Log Format

**Centralized log:**
```
[2026-02-13 10:30:00] [INFO] [Registry] Agent registered: PDF Parser
[2026-02-13 10:30:15] [INFO] [Paper Analyzer] Calling extract_text
[2026-02-13 10:30:17] [INFO] [PDF Parser] Operation completed (2.3s, $0.05)
```

### System Status

**Check all agents:**
```bash
./check_status.sh
```

**Output:**
```
==========================================
📊 aFDO System Status
==========================================

Registry (8000):         ✅ Running (PID 12345)
PDF Parser (8004):       ✅ Running (PID 12350)
FAIR Assessor (8005):    ✅ Running (PID 12351)
Creator (8006):          ✅ Running (PID 12352)
LLM GPT-4 (8007):        ✅ Running (PID 12353)
LLM GPT-4-mini (8008):   ✅ Running (PID 12354)
Wikipedia (8010):        ✅ Running (PID 12355)
ArXiv (8011):            ✅ Running (PID 12356)
Open Library (8012):     ✅ Running (PID 12357)
Paper Analyzer (8003):   ✅ Running (PID 12358)
NL Handler (8002):       ✅ Running (PID 12359)
LLM Consultant (8014):   ✅ Running (PID 12360)
Chat UI (8001):          ✅ Running (PID 12361)

Summary: 13/13 agents running
```

**Check registry health:**
```bash
curl http://localhost:8000/health
```

**Check specific agent:**
```bash
curl http://localhost:8004/
```

---

## Troubleshooting

### Common Issues

#### Port Already in Use

**Symptom:**
```
❌ ERROR: Port 8000 already in use!
```

**Solution:**
```bash
# Stop the system
./stop_system.sh

# Or kill specific port
lsof -ti:8000 | xargs kill

# Restart
./start_system.sh
```

#### API Key Not Set

**Symptom:**
```
⚠️  Warning: OPENAI_API_KEY not set
```

**Solution:**
```bash
# Set via environment
export OPENAI_API_KEY='sk-...'

# Or create .env file
echo "OPENAI_API_KEY='sk-...'" > .env

# Restart
./stop_system.sh && ./start_system.sh
```

#### Agent Failed to Start

**Symptom:**
```
❌ PDF Parser failed to start! Check logs/pdf-parser.log
```

**Solution:**
```bash
# Check agent log
cat logs/pdf-parser.log

# Common causes:
# 1. Missing dependencies
pip install -r requirements.txt

# 2. Registry not ready
# Wait 3-5 seconds after registry starts

# 3. Port conflict
lsof -i :8004
```

#### No Agents Found for Operation

**Symptom:**
```
ValueError: No agents found for operation 'extract_text'
```

**Solution:**
```bash
# Verify agents registered
curl http://localhost:8000/market/agents/by_operation/extract_text

# If empty, restart agent
pkill -f pdf_parser_agent
python3 agents/pdf_parser/pdf_parser_agent.py &

# Check logs
tail -f logs/pdf-parser.log
```

#### Budget Exceeded

**Symptom:**
```
{"status": "insufficient_budget", "message": "Cost estimate exceeds budget"}
```

**Solution:**
- Increase budget allocation
- Use "cheapest" policy
- Simplify query to require fewer operations

#### Slow Response

**Possible causes:**
1. LLM API latency (OpenAI)
2. Large PDF processing
3. Complex workflow with many steps
4. Agent queue buildup

**Solutions:**
- Use "fastest" policy
- Reduce PDF size
- Increase budget for parallel processing
- Check agent queue depth

### Debug Mode

**Enable verbose logging:**
```bash
export LOG_LEVEL=DEBUG
./stop_system.sh
./start_system.sh
```

**View detailed logs:**
```bash
tail -f logs/afdo_$(date +%Y-%m-%d).log
```

### Getting Help

1. **Check logs:** `logs/` directory
2. **Check status:** `./check_status.sh`
3. **Check registry:** `curl http://localhost:8000/`
4. **Check ports:** `lsof -i :8000-8014`
5. **Review documentation:** `ARCHITECTURE.md`, `DEVELOPER_GUIDE.md`

### Clean Restart

If all else fails:

```bash
# Stop everything
./stop_system.sh

# Kill any remaining processes
pkill -9 -f "python3.*(registry|agents)"

# Clean logs (optional)
rm -rf logs/*

# Restart fresh
./start_system.sh
```

---

## System Administration

### Stopping the System

```bash
./stop_system.sh
```

**What happens:**
1. Stops agents in reverse order
2. Uses PID files from `logs/`
3. Sends SIGTERM (graceful)
4. Force kill (SIGKILL) if needed
5. Cleans up PID files
6. Verifies all stopped

### Restarting Agents

**Restart single agent:**
```bash
# Stop agent
pkill -f pdf_parser_agent

# Start agent
python3 agents/pdf_parser/pdf_parser_agent.py &

# Verify
curl http://localhost:8004/
```

**Restart all agents:**
```bash
./stop_system.sh
./start_system.sh
```

### Performance Monitoring

**Check system resources:**
```bash
# CPU and memory
ps aux | grep python3 | grep -E "(registry|agents)"

# Disk usage
du -sh logs/
```

**Monitor agent load:**
```bash
curl http://localhost:8000/status/agents
```

**Monitor specific agent:**
```bash
curl http://localhost:8000/status/agent/21.T11148/afdo-pdf-parser
```

### Backup and Restore

**Backup registry data:**
```bash
tar -czf registry-backup-$(date +%Y%m%d).tar.gz registry/data/
```

**Restore registry data:**
```bash
tar -xzf registry-backup-20260213.tar.gz
```

**Backup logs:**
```bash
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/
```

### System Requirements

**Minimum:**
- Python 3.10+
- 2 GB RAM
- 1 GB disk space

**Recommended:**
- Python 3.11+
- 4 GB RAM
- 2 GB disk space
- SSD storage

**Network:**
- Localhost only (127.0.0.1)
- Ports 8000-8014 must be available
- Internet access for OpenAI API

---

## Extending the System

### Adding New aFDOs

Want to add a new agent to the system? Here's a quick overview:

**Requirements Checklist:**

✅ **Must Have:**
- Inherit from `aFDOBase`
- Implement `handle_operation()` (async)
- Implement `get_self_description()`
- Unique port number (check ports 8000-8014 are used)
- Valid FDO type (e.g., `21.T11148/type-data-source-v1`)
- Policy file (`agents/<name>/policy.json`)

✅ **Should Have:**
- Input validation
- Error handling
- Cost estimation
- Unit tests
- Documentation

**Quick Example:**

```python
from shared.afdo_base import aFDOBase

class MyAgent(aFDOBase):
    def __init__(self):
        super().__init__(
            name="My Agent",
            fdo_type="21.T11148/type-data-source-v1",
            operations=["my_operation"],
            port=8015,
            cost=0.10
        )

    async def handle_operation(self, operation, caller_pid, parameters):
        if operation == "my_operation":
            # Validate input
            query = parameters.get("query")
            if not query:
                raise ValueError("Missing 'query' parameter")

            # Do work
            result = f"Processed: {query}"

            # Return structured response
            return {
                "result": result,
                "processor": self.pid
            }
        else:
            raise ValueError(f"Unknown operation: {operation}")

    def get_self_description(self):
        return {
            "agent_info": {
                "name": "My Agent",
                "version": "1.0.0",
                "agent_type": "data_source"
            },
            "capabilities": {
                "my_operation": {
                    "operation_type": "data_retrieval",
                    "input_schema": {
                        "required": ["query"],
                        "properties": {"query": {"type": "string"}}
                    }
                }
            }
        }

if __name__ == "__main__":
    agent = MyAgent()
    agent.run()
```

**Deployment Steps:**

1. Create agent file: `agents/my_agent/my_agent_agent.py`
2. Create policy: `agents/my_agent/policy.json`
3. Add to `start_system.sh`
4. Test standalone: `python3 agents/my_agent/my_agent_agent.py`
5. Restart system: `./stop_system.sh && ./start_system.sh`
6. Verify: `./check_status.sh`

**Complete Guides:**

- **For Architecture:** See [ARCHITECTURE.md - How to Add a New aFDO](ARCHITECTURE.md#how-to-add-a-new-afdo)
- **For Development:** See [DEVELOPER_GUIDE.md - Creating New Agents](DEVELOPER_GUIDE.md#creating-new-agents)

**Available Agent Types:**

| Type | Purpose | Example |
|------|---------|---------|
| **Task Agent** | Single operation, no delegation | PDF Parser |
| **Composite Agent** | Multi-step workflows, orchestrates others | Paper Analyzer |
| **Data Source Agent** | External API integration | Wikipedia, ArXiv |
| **Interface Agent** | User-facing entry points | Chat UI |
| **Meta Agent** | System-level operations | Creator |

**Available Ports:** 8013, 8015+ (check with `./check_status.sh`)

### Modifying Existing Agents

**To add new operation to existing agent:**

1. Add operation to `operations=[]` list in `__init__`
2. Add capability to `get_self_description()`
3. Add handler in `handle_operation()`
4. Implement the operation method
5. Update policy file if needed
6. Restart agent

**Example:** Adding `search_books` to Open Library Agent

```python
# In __init__
operations=["get_book_info", "search_books"]  # Added search_books

# In handle_operation
elif operation == "search_books":
    return await self._search_books(parameters)

# Implement method
async def _search_books(self, parameters):
    query = parameters.get("query")
    # Implementation...
```

See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for complete instructions.

---

## Next Steps

- **Learn the Architecture:** Read [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- **Extend the System:** Read [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for development and agent documentation
- **Review Policies:** See `agents/*/policy.json` for agent-specific policy configurations

---

## Support and Resources

- **Documentation:** See `docs/` directory
- **Examples:** See `workflows/examples/`
- **Tests:** Run `pytest tests/`
- **Issues:** Check logs first, then system status

---

**Document Version:** 2.0.0
**Last Verified:** 2026-02-15
**Tested On:** Ubuntu 22.04, macOS 13
**Maintainer:** aFDO Development Team
