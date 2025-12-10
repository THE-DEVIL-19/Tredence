# Mini Agent Workflow Engine

A minimal graph-based workflow engine built with FastAPI.

It supports:

- Nodes representing tools
- Edges with optional conditions
- Branching based on state
- Loops (edges that go back to previous nodes)
- Shared mutable state through the workflow
- Execution logs for each run

Includes a sample **Code Review Mini-Agent** workflow.

## Project structure

```text
app/
  __init__.py
  models.py
  storage.py
  registry.py
  engine.py
  workflows.py
  main.py
requirements.txt
README.md
