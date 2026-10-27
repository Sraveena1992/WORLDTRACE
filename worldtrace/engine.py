"""WORLDTRACE mission execution with validated dependencies and explicit model provenance."""
import json
import threading
from . import agent, storage, tools, verification, recovery

AGENT_NAMES = {"pdf_inspect":"Document Analyst","email_inspect":"Communications Analyst","network_inspect":"Network Investigator","etl_compare":"Data Integrity Agent","database_check":"Database Auditor","api_virtualize":"API Simulator","performance_probe":"Performance Engineer","middleware_test":"Integration Tester","mainframe_contract":"Legacy Systems Analyst"}

def start(goal, mode="local"):
    if mode not in ("local", "model"):
        raise ValueError("Unknown mode")
    if mode == "model" and not agent.configured():
        raise agent.ModelUnavailable("Meta inference not configured. Use local non-AI workflow or configure a real endpoint.")
    mid = storage.make_mission(goal, mode)
    storage.event(mid, "mission.created", {"goal": goal, "mode": mode, "scope": "synthetic local fixtures only"})
    threading.Thread(target=run, args=(mid, goal, mode), daemon=True).start()
    return mid

def run(mid, goal, mode):
    try:
        storage.update_mission(mid, "planning")
        plan = agent.make_plan(goal, mode == "model")
        storage.event(mid, "plan.generated", plan)
        task_map = {}
        for idx, step in enumerate(plan["steps"]):
            task_map[step["id"]] = (storage.add_task(mid, AGENT_NAMES[step["tool"]], step["tool"], idx), step)
        storage.update_mission(mid, "running")
        states = {}
        for step_id, (tid, step) in task_map.items():
            tool = step["tool"]
            blockers = [dep for dep in step["depends_on"] if states.get(dep) in ("error", "blocked")]
            if blockers:
                result = {"blocked_by": blockers, "reason": "Required upstream execution failed"}
                storage.update_task(tid, "blocked", result)
                states[step_id] = "blocked"
                storage.event(mid, "task.blocked", {"step_id": step_id, "task_id": tid, "dependencies": blockers})
                continue
            storage.update_task(tid, "running")
            storage.event(mid, "tool.started", {"step_id": step_id, "depends_on": step["depends_on"], "tool": tool, "task_id": tid, "agent": AGENT_NAMES[tool]})
            try:
                result = tools.execute(tool)
                status = "passed" if result.get("pass") else "finding"
                storage.update_task(tid, status, result)
                states[step_id] = status
                storage.event(mid, "tool.completed", {"step_id": step_id, "tool": tool, "task_id": tid, "status": status, "result": result})
            except Exception as exc:
                result = {"error": str(exc)[:250]}
                storage.update_task(tid, "error", result)
                states[step_id] = "error"
                storage.event(mid, "tool.failed", {"step_id": step_id, "tool": tool, "task_id": tid, "error": result["error"]})
        details = storage.get(mid)
        findings = verification.verify(details["tasks"])
        storage.event(mid, "verification.completed", findings)
        proposals = recovery.recommend(details["tasks"])
        storage.event(mid, "recovery.proposed", {"proposals": proposals, "human_review_required": True, "executed": False})
        report = ["# WORLDTRACE | Mission Evidence Report", "",
                  f"**Mission:** {mid}", f"**Goal:** {goal}", f"**Execution mode:** {mode}",
                  f"**Plan provenance:** {plan['mode']}", f"**Verification:** {findings['verdict']}", "",
                  "## Plan", f"**Reason:** {plan['reason']}", ""]
        for step in plan["steps"]:
            report.append(f"- `{step['id']}` → `{step['tool']}` (depends on: {', '.join(step['depends_on']) or 'none'})")
        report += ["", "## Tool results"]
        for item in details["tasks"]:
            report += [f"### {item['name']} — {item['status']}", "```json", json.dumps(item["result"], indent=2, default=str), "```", ""]
        report += ["## Human-reviewed recovery proposals (NOT EXECUTED)", ""]
        if proposals:
            for proposal in proposals:
                report.append(f"- **{proposal['tool']}** [{proposal['status']}]: {proposal['proposed_action']} Owner: {proposal['owner']}. Human approval required.")
        else:
            report.append("- No corrective action proposals needed for the executed fixture checks.")
        report += ["", "## Deterministic cross-tool checks", "```json", json.dumps(findings["cross_checks"], indent=2), "```", "",
                   "## Reliability notes",
                   "- Evidence originates from synthetic LOCAL sample fixtures.",
                   "- AI planning occurs only when model mode logged a successful actual provider response.",
                   "- No external mail, real-world remediation, production writes, or physical truth certification.",
                   "- Hash chaining indicates internal record consistency within a trusted database, not externally anchored proof."]
        target = storage.root() / "reports"
        target.mkdir(exist_ok=True)
        (target / f"{mid}.md").write_text("\n".join(report), encoding="utf-8")
        storage.event(mid, "report.generated", {"artifact": f"{mid}.md", "verdict": findings["verdict"]})
        storage.update_mission(mid, "completed")
    except Exception as exc:
        storage.event(mid, "mission.error", {"error": str(exc)[:450]})
        storage.update_mission(mid, "error", str(exc)[:450])
