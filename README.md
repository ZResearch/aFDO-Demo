[![Video](https://github.com/user-attachments/assets/3db44408-517a-4200-bd1e-65657cf14743)]

https://github.com/user-attachments/assets/3db44408-517a-4200-bd1e-65657cf14743

# aFDO — Autonomous FAIR Digital Objects

**aFDO** is a multi-agent marketplace for scientific knowledge processing built on [FAIR Digital Object](https://fairdo.org/) principles. Agents register themselves in a central registry, discover each other at runtime via semantic capability matching, and delegate tasks autonomously based on configurable JSON policies — with no hardcoded workflows.

Submitted to **CIKM 2026**.

---

## Quick Start

```bash
# 1. Set your OpenAI API key
export OPENAI_API_KEY='sk-...'

# 2. Install dependencies (inside a virtualenv recommended)
pip install -r requirements.txt

# 3. Start all agents
./start_system.sh

# 4. Open the web interface
open http://localhost:8001/ui

# 5. Stop when done
./stop_system.sh
```

Check running status at any time with `./check_status.sh`.

---

## System Overview

```
User
 └─► Chat UI (8001)
          │ queries registry for best agent
          ▼
     Registry (8000)  ──  semantic discovery, FDO storage, reputation
          │ returns ranked candidates
          ▼
     Agent Marketplace (peer-to-peer calls after discovery)
     ┌─────────────────────┬──────────────────────────────────┐
     │  Composite Agents   │  Task & Data Agents              │
     │  Paper Analyzer     │  PDF Parser · FAIR Assessor      │
     │  NL Handler         │  LLM GPT-4 · LLM GPT-4-mini     │
     │  LLM Consultant     │  Wikipedia · ArXiv · OpenLibrary │
     │                     │  Fact Checker · Creator           │
     └─────────────────────┴──────────────────────────────────┘
```

Each agent is an independent FastAPI service. Discovery uses multi-objective scoring — `score = α·semantic + β·reputation − γ·cost` — so the registry selects the most relevant, reliable, and cost-effective provider automatically.

---

## Agents

| Agent | Port | Category | Purpose |
|---|---|---|---|
| Registry | 8000 | Infrastructure | FDO storage, discovery, reputation |
| Chat UI | 8001 | Interface | User entry point, query routing |
| NL Handler | 8002 | Composite | Scientific natural-language processing |
| Paper Analyzer | 8003 | Composite | Full research paper analysis |
| PDF Parser | 8004 | Task | Text and metadata extraction |
| FAIR Assessor | 8005 | Task | FAIR compliance scoring |
| Creator | 8006 | Meta | Dynamic agent creation |
| LLM GPT-4 | 8007 | Task | General-purpose LLM service |
| LLM GPT-4-mini | 8008 | Task | Cost-effective LLM service |
| Wikipedia | 8010 | Data Source | Wikipedia knowledge retrieval |
| ArXiv | 8011 | Data Source | Scientific paper search |
| Open Library | 8012 | Data Source | Book and reference lookup |
| Fact Checker | 8013 | Composite | Multi-source fact verification |
| LLM Consultant | 8014 | Composite | Workflow generation |

---

## Web Interfaces

| Interface | URL | Description |
|---|---|---|
| Chat UI | http://localhost:8001/ui | Submit queries, view execution traces |
| Registry Monitor | http://localhost:8000/monitor | Live agent network and activity log |

---

## Requirements

- Python 3.10+, Linux or macOS
- OpenAI API key (`OPENAI_API_KEY`)
- Ports 8000–8014 available

---

## Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** — system design, semantic discovery algorithm, cascading delegation, policy engine, reputation system, execution traces, FDO compliance
- **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** — environment setup, project structure, creating new agents, policy configuration, testing procedures, debugging

---

## Implementation Notes

This implementation was developed with assistance from AI coding tools for (partial) code generation, debugging, and documentation. All architectural decisions, algorithm design, and system evaluation were performed by the authors.
