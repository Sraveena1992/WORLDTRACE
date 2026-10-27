"""Validate untrusted model-generated tool plans and topologically sort dependencies."""
from .tools import AVAILABLE

class InvalidPlan(ValueError):
    pass

def validate_plan(raw):
    if not isinstance(raw, dict):
        raise InvalidPlan("Plan must be an object")
    if "steps" in raw:
        incoming = raw["steps"]
    elif "tasks" in raw:
        tasks = raw["tasks"]
        if not isinstance(tasks, list):
            raise InvalidPlan("Tasks must be an array")
        incoming = [{"id": f"step_{i+1}", "tool": tool, "depends_on": [], "objective": "Inspect approved fixture"} for i, tool in enumerate(tasks)]
    else:
        raise InvalidPlan("Plan has no steps")
    if not isinstance(incoming, list) or not 2 <= len(incoming) <= len(AVAILABLE):
        raise InvalidPlan("Plan must have 2 to 9 steps")
    steps = []
    ids, used = set(), set()
    for item in incoming:
        if not isinstance(item, dict):
            raise InvalidPlan("Invalid step")
        sid, tool, deps = item.get("id"), item.get("tool"), item.get("depends_on", [])
        if not isinstance(sid, str) or not sid or len(sid) > 48 or any(not (c.isalnum() or c in "_-") for c in sid):
            raise InvalidPlan("Invalid step id")
        if sid in ids or tool in used:
            raise InvalidPlan("Duplicate step id or tool")
        if not isinstance(tool, str) or tool not in AVAILABLE:
            raise InvalidPlan("Tool not allowlisted")
        if not isinstance(deps, list) or any(not isinstance(d, str) for d in deps) or len(deps) != len(set(deps)):
            raise InvalidPlan("Invalid dependencies")
        objective = item.get("objective", "Inspect approved fixture")
        if not isinstance(objective, str):
            raise InvalidPlan("Invalid objective")
        ids.add(sid)
        used.add(tool)
        steps.append({"id": sid, "tool": tool, "depends_on": deps, "objective": objective[:220]})
    for step in steps:
        if step["id"] in step["depends_on"] or any(dep not in ids for dep in step["depends_on"]):
            raise InvalidPlan("Unknown or self dependency")
    ordered, done, remaining = [], set(), list(steps)
    while remaining:
        ready = [s for s in remaining if all(d in done for d in s["depends_on"])]
        if not ready:
            raise InvalidPlan("Circular dependency")
        for s in ready:
            ordered.append(s)
            done.add(s["id"])
            remaining.remove(s)
    return {"reason": str(raw.get("reason", ""))[:350], "steps": ordered, "tasks": [s["tool"] for s in ordered]}
