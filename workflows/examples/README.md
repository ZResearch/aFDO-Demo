# Workflow Examples

**⚠️ IMPORTANT: These are EXAMPLES ONLY**

## Purpose

These JSON files are provided as **documentation and reference examples** only. They demonstrate the structure and capabilities of the workflow system, but **they are NOT used by the live system**.

## How the System Actually Works

The aFDO system **does NOT use predefined workflow templates**. Instead:

1. **Agent encounters complex task** → Policy engine evaluates complexity
2. **Policy triggers "consult_for_workflow"** → Agent queries registry for LLM Consultant
3. **LLM Consultant generates custom workflow** → Uses GPT-4 to analyze task and create workflow on-the-fly
4. **Workflow executed dynamically** → Generated workflow loaded into workflow engine and executed

## Key Principle

**NO HARDCODED WORKFLOWS!**

Every task gets a custom-generated workflow tailored to:
- The specific task requirements
- Available agent capabilities
- Budget constraints
- Quality preferences
- Current system state

## Example Workflows

The files in this directory show what workflows CAN look like:

1. **`simple_research_workflow.json`**
   - Example: Basic 4-step research workflow
   - Shows: Sequential steps with fallback handling

2. **`multi_source_research_workflow.json`**
   - Example: Parallel data gathering from multiple sources
   - Shows: Independent parallel steps with "continue on failure"

3. **`budget_aware_workflow.json`**
   - Example: Cost-adaptive workflow with budget limits
   - Shows: Selection criteria based on cost

## For Developers

If you want to understand workflow structure:
- ✅ Read these examples
- ✅ Study the workflow schema in `shared/protocols/workflow_protocol.json`
- ✅ See `shared/protocols/workflow_engine.py` for execution logic
- ✅ See `agents/llm_consultant/llm_consultant_agent.py` for generation logic

If you want to modify workflow behavior:
- ❌ Do NOT edit these JSON files (they're not used!)
- ✅ Modify the LLM Consultant's prompts
- ✅ Update agent policies to change when workflows are used
- ✅ Enhance the workflow engine's capabilities

## Architecture Shift

**Before (TASK 25 Parts 1-6):**
```
Agent → Load predefined workflow → Execute
```

**Now (Updated TASK 25):**
```
Agent → Consult LLM → Generate workflow → Execute
```

This shift enables:
- ✅ True autonomy - no hardcoded assumptions
- ✅ Adaptability - workflows tailored to each task
- ✅ Intelligence - LLM understands context and requirements
- ✅ Flexibility - system evolves without code changes

## Related Documentation

- **Task specification**: `/home/boukhers/IJCAI_DEMO/task` (lines 1-488)
- **LLM Consultant**: `agents/llm_consultant/llm_consultant_agent.py`
- **Workflow engine**: `shared/protocols/workflow_engine.py`
- **Policy system**: `shared/policy_engine.py`
- **Integration**: `shared/afdo_base.py` (_consult_for_workflow method)

---

**Remember**: These examples are for learning and reference. The actual system generates workflows dynamically!
