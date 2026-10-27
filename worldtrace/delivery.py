"""Constrained delivery workflow producing real artifacts from a bounded user request.

The 'local' route is deterministic and not AI reasoning. No external calls/writes.
The workflow uses six functional stages with recorded evidence.
"""
from __future__ import annotations
import hashlib
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile, ZIP_DEFLATED

from .storage import root

MAX_EVIDENCE = 12000
ALLOWED = {"supplier_onboarding", "api_incident", "data_quality"}

def _utc():
    return datetime.now(timezone.utc).isoformat()

def _sha(data: bytes):
    return hashlib.sha256(data).hexdigest()

def _safe_text(value: str):
    return value.strip().replace("\x00", "")

def validate(goal: str, evidence: str, domain: str):
    if domain not in ALLOWED:
        raise ValueError("Unsupported workflow domain")
    if len(goal.strip()) < 12 or len(goal) > 1500:
        raise ValueError("Goal must contain 12-1500 characters")
    if len(evidence) > MAX_EVIDENCE:
        raise ValueError("Evidence exceeds 12000 characters")
    return _safe_text(goal), _safe_text(evidence)

def _facts(evidence: str):
    lines = [line.strip() for line in evidence.splitlines() if line.strip()]
    return lines[:60]

def _risks(lines: list[str]):
    indicators = ("missing", "fail", "error", "503", "unsigned", "pending", "duplicate", "mismatch", "incomplete")
    return [line for line in lines if any(k in line.lower() for k in indicators)][:20]

def produce(goal: str, evidence: str, domain: str = "supplier_onboarding"):
    goal, evidence = validate(goal, evidence, domain)
    rid = "WD-" + uuid4().hex[:12].upper()
    folder = (root() / "deliverables" / rid).resolve()
    approved = (root() / "deliverables").resolve()
    if not folder.is_relative_to(approved):
        raise ValueError("Invalid output directory")
    folder.mkdir(parents=True, exist_ok=False)
    events = []
    def record(agent, operation, details):
        events.append({"sequence": len(events)+1, "agent": agent, "operation": operation,
                       "time": _utc(), "details": details})
    facts = _facts(evidence)
    risks = _risks(facts)
    record("Research Agent", "extract_user_supplied_evidence",
           {"facts": len(facts), "risk_signals": len(risks), "source": "user-provided text; no external research"})
    actions = []
    for ix, risk in enumerate(risks, start=1):
        actions.append({"id": f"A{ix:02d}", "observation": risk[:250],
                        "recommended_action": "Assign a human owner to investigate, correct in an authorized environment, and reverify.",
                        "status": "PROPOSED_NOT_EXECUTED", "requires_approval": True})
    if not actions:
        actions.append({"id": "A01", "observation": "No explicit error keyword in submitted evidence",
                        "recommended_action": "Obtain additional source evidence and confirm the requested outcome.",
                        "status": "PROPOSED_NOT_EXECUTED", "requires_approval": True})
    record("Builder Agent", "build_resolution_plan",
           {"action_count": len(actions), "method": "deterministic keyword triage, not AI-generated"})
    heading = {
        "supplier_onboarding": "Supplier onboarding exception",
        "api_incident": "API incident",
        "data_quality": "Data quality exception"
    }[domain]
    report = [
        "# WORLDTRACE | Evidence-to-Delivery Package", "",
        f"**Package ID:** {rid}", f"**Domain:** {heading}", f"**Objective:** {goal}",
        "**Provenance:** User-supplied evidence, deterministic local processing; NOT Meta inference.",
        "**Outcome:** Analysis package produced. No real-world remediation executed.", "",
        "## Research observations", "",
    ]
    report.extend(f"- {line}" for line in facts or ["No supporting evidence supplied."])
    report += ["", "## Risks flagged for human verification", ""]
    report.extend(f"- {risk}" for risk in risks or ["No explicit failures detected in the supplied text."])
    report += ["", "## Proposed next steps", ""]
    report.extend(f"- **{a['id']}** — {a['recommended_action']} Evidence: {a['observation']}" for a in actions)
    report += ["", "## Verification boundaries",
               "- The submitted text has not been independently verified.",
               "- No external service, inbox, database or production system was contacted.",
               "- No correction, deployment, message sending or approval was executed.",
               "- Artifacts were written only under the controlled WORLDTRACE deliverables directory.",
               "- A human should verify facts and approve any consequential action.", ""]
    documents = {
        "research_brief.md": ("\n".join(report) + "\n").encode("utf-8"),
        "action_plan.json": (json.dumps({"package_id": rid, "domain": domain,
                                         "goal": goal, "actions": actions}, indent=2) + "\n").encode("utf-8"),
        "evidence.json": (json.dumps({"package_id": rid, "source": "user_supplied",
                                      "evidence": evidence, "fact_count": len(facts)}, indent=2) + "\n").encode("utf-8"),
    }
    record("Security Agent", "approve_scoped_writes",
           {"files": sorted(documents), "root": "WORLDTRACE_DATA_DIR/deliverables", "external_writes": False})
    hashes = {}
    for filename, payload in documents.items():
        target = folder / filename
        target.write_bytes(payload)
        hashes[filename] = _sha(payload)
    record("Execution Agent", "write_artifacts", {"files_written": len(documents), "hashes": hashes})
    checked = {}
    for filename, expected in hashes.items():
        target = folder / filename
        checked[filename] = target.exists() and _sha(target.read_bytes()) == expected
    parsed = json.loads((folder / "action_plan.json").read_text(encoding="utf-8"))
    checked["action_plan_schema"] = parsed.get("package_id") == rid and len(parsed.get("actions", [])) >= 1
    verified = all(checked.values())
    record("Verification Agent", "verify_files_and_schema",
           {"passed": verified, "checks": checked})
    manifest = {"package_id": rid, "domain": domain, "goal": goal,
                "status": "DELIVERED_LOCAL_PACKAGE" if verified else "FAILED_VERIFICATION",
                "execution_mode": "deterministic_local", "files": hashes,
                "verification": checked, "approved_external_actions": 0,
                "limitations": "No Meta-model inference and no independently verified external outcome"}
    if not verified:
        raise RuntimeError("Independent file verification failed")
    manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode()
    (folder / "manifest.json").write_bytes(manifest_bytes)
    record("Delivery Agent", "package_verified_artifacts",
           {"package": f"{rid}.zip", "files": list(documents)+["manifest.json", "trace.json"]})
    trace_bytes = (json.dumps(events, indent=2) + "\n").encode()
    (folder / "trace.json").write_bytes(trace_bytes)
    package = folder / f"{rid}.zip"
    with ZipFile(package, "w", compression=ZIP_DEFLATED) as z:
        for name in [*documents, "manifest.json", "trace.json"]:
            z.write(folder/name, arcname=name)
    with ZipFile(package) as z:
        if z.testzip() is not None:
            raise RuntimeError("Package integrity check failed")
        assert all(name in z.namelist() for name in [*documents, "manifest.json", "trace.json"])
    response = {"id": rid, "mode": "deterministic_local", "domain": domain, "status": manifest["status"],
                "events": events, "verification": checked, "files": list(documents)+["manifest.json", "trace.json"],
                "download_url": f"/api/deliverables/{rid}/download",
                "scope": "User supplied text processed locally; no external changes or AI inference"}
    return response
