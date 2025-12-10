# app/storage.py

from typing import Dict
from .models import GraphDefinition, RunState

# In-memory stores (simple for the assignment)
graphs: Dict[str, GraphDefinition] = {}
runs: Dict[str, RunState] = {}
