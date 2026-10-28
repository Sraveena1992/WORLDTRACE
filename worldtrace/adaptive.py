"""Bounded model-guided follow-up for WORLDTRACE Mission Commander.

Only model-mode missions may request a second plan. The response is never
trusted to run arbitrary code: all suggested tools are allowlisted, never
repeat a tool, and cannot exceed a fixed total budget. This module does not
claim independent verification of real-world evidence.
"""
from .planning import validate_plan, InvalidPlan
from .tools import AVAILABLE

MAX_TOTAL_TOOLS = 9
MAX_FOLLOWUP_TOOLS = 3

def followup_candidates(executed):
    return sorted(AVAILABLE - set(executed))

def validate_followup(raw, executed):
    """Validate a second-round model response against the remaining tool budget."""
    if not isinstance(raw, dict):
        raise InvalidPlan("Follow-up must be an object")
    if raw.get("finish") is True:
        return {"finish": True, "reason": str(raw.get("reason", ""))[:350], "steps": [], "tasks": []}
    remaining = followup_candidates(executed)
    incoming = raw.get("steps", [])
    if not isinstance(incoming, list) or not 1 <= len(incoming) <= min(MAX_FOLLOWUP_TOOLS, len(remaining)):
        raise InvalidPlan("Follow-up must contain 1-3 new tools")
    used, ids = set(), set()
    steps = []
    for item in incoming:
        if not isinstance(item, dict):
            raise InvalidPlan("Invalid follow-up step")
        sid, tool = item.get("id"), item.get("tool")
        if not isinstance(sid, str) or not sid or len(sid) > 48 or not all(c.isalnum() or c in "_-" for c in sid):
            raise InvalidPlan("Invalid follow-up id")
        if sid in ids or tool in used or tool not in remaining:
            raise InvalidPlan("Repeated or unauthorized tool")
        # Follow-up is a new execution round; dependencies are internal to the round.
        deps = item.get("depends_on", [])
        if not isinstance(deps, list) or len(deps) != len(set(deps)) or any(not isinstance(d, str) for d in deps):
            raise InvalidPlan("Invalid follow-up dependencies")
        ids.add(sid)
        used.add(tool)
        objective = item.get("objective", "Inspect remaining approved fixture")
        if not isinstance(objective, str):
            raise InvalidPlan("Invalid follow-up objective")
        steps.append({"id": sid, "tool": tool, "depends_on": deps, "objective": objective[:220]})
    if any(d not in ids or d == s["id"] for s in steps for d in s["depends_on"]):
        raise InvalidPlan("Unknown or self-dependency")
    ordered, completed, pending = [], set(), list(steps)
    while pending:
        available = [s for s in pending if all(d in completed for d in s["depends_on"])]
        if not available:
            raise InvalidPlan("Cyclic follow-up plan")
        for step in available:
            ordered.append(step)
            completed.add(step["id"])
            pending.remove(step)
    return {"finish": False, "reason": str(raw.get("reason", ""))[:350],
            "steps": ordered, "tasks": [s["tool"] for s in ordered]}
