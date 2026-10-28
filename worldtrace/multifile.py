"""A bounded multi-file mission, with verified outputs and no AI claim."""
import hashlib
import json
from datetime import datetime, timezone
from . import uploads

FIELDS = {"pdf": ("pdf_inspect", ".pdf"), "email": ("email_inspect", ".eml"),
          "har": ("network_inspect", ".har"), "source_csv": ("etl_compare", ".csv"),
          "target_csv": ("etl_compare", ".csv"), "api_json": ("api_virtualize", ".json"),
          "messages_json": ("middleware_test", ".json"),
          "legacy_txt": ("mainframe_contract", ".txt")}
MAX_TOTAL = 8 * 1024 * 1024

def _event(events, role, action, details):
    previous = events[-1]["hash"] if events else "GENESIS"
    stamp = datetime.now(timezone.utc).isoformat()
    canonical = json.dumps({"role": role, "action": action, "details": details,
                            "prev": previous, "time": stamp}, sort_keys=True)
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    events.append({"role": role, "action": action, "details": details,
                   "time": stamp, "prev_hash": previous, "hash": digest})

def run(goal, files):
    if not isinstance(goal, str) or not 12 <= len(goal.strip()) <= 1500:
        raise ValueError("Instruction must be 12-1500 characters")
    if not 1 <= len(files) <= len(FIELDS) or set(files) - set(FIELDS):
        raise ValueError("Provide one to eight recognized file roles")
    if ("source_csv" in files) != ("target_csv" in files):
        raise ValueError("ETL requires both source_csv and target_csv")
    if sum(len(data) for _, data in files.values()) > MAX_TOTAL:
        raise ValueError("Combined file size exceeds 8 MiB")
    for role, (filename, data) in files.items():
        if not filename.lower().endswith(FIELDS[role][1]) or not 1 <= len(data) <= uploads.MAX_BYTES:
            raise ValueError("Invalid or oversized file for role " + role)
    events = []
    _event(events, "Research Agent", "inventory_user_evidence",
           {"roles": sorted(files), "source": "user supplied"})
    _event(events, "Security Agent", "enforce_bounded_parsers",
           {"external_calls": 0, "external_writes": 0, "model_calls": 0})
    observations = []
    for role in sorted(files):
        if role == "target_csv":
            continue
        filename, data = files[role]
        comparison = files["target_csv"][1] if role == "source_csv" else None
        finding = uploads.inspect(FIELDS[role][0], filename, data, comparison)
        observations.append({"role": role, **finding})
        _event(events, "Execution Agent", "inspect_real_file",
               {"role": role, "file": finding["file_name"],
                "status": finding["status"], "sha256": finding["sha256"]})
    by_role = {item["role"]: item for item in observations}
    checks = []
    if "har" in by_role and "api_json" in by_role:
        statuses = {f["status"] for f in by_role["har"]["result"]["failures"]}
        simulated = by_role["api_json"]["result"]["simulated_status"]
        checks.append({"name": "HAR and API status consistency",
                       "matched": simulated in statuses,
                       "basis": "Recorded HAR versus simulated API JSON; not real service confirmation",
                       "observed_statuses": sorted(statuses), "simulated_status": simulated})
    findings = [item for item in observations if item["status"] != "passed"]
    verdict = "REVIEW_NEEDED" if findings or any(not check["matched"] for check in checks) else "LOCAL_CHECKS_PASSED"
    _event(events, "Verification Agent", "compare_evidence_and_checks",
           {"verdict": verdict, "cross_checks": checks, "findings": len(findings)})
    actions = [{"file": item["file_name"], "tool": item["tool"],
                "next_action": "Human must investigate, authorize changes, then rerun verification.",
                "executed": False} for item in findings]
    _event(events, "Builder Agent", "prepare_review_actions",
           {"proposals": len(actions), "executed": 0})
    report_lines = ["# WORLDTRACE Multi-File Evidence Report", "",
                    "Instruction: " + goal.strip(), "Verdict: " + verdict,
                    "Mode: deterministic; NOT Meta model inference", "",
                    "## Uploaded evidence"]
    for item in observations:
        report_lines += ["", "### " + item["file_name"],
                         "Tool: " + item["tool"], "Status: " + item["status"],
                         "SHA-256: " + item["sha256"],
                         json.dumps(item["result"], indent=2, ensure_ascii=False)]
    report_lines += ["", "## Cross-file consistency", json.dumps(checks, indent=2),
                     "", "## Human review recommendations", json.dumps(actions, indent=2),
                     "", "## Limits",
                     "No real-world remediation, production access, external writes or model inference."]
    report = "\n".join(report_lines) + "\n"
    digest = hashlib.sha256(report.encode()).hexdigest()
    _event(events, "Delivery Agent", "produce_verified_markdown",
           {"report_sha256": digest, "bytes": len(report.encode())})
    return {"mode": "deterministic_multi_file", "status": verdict,
            "goal": goal.strip(), "observations": observations,
            "cross_checks": checks, "proposed_actions": actions, "trace": events,
            "report_markdown": report, "report_sha256": digest,
            "privacy": "Uploaded inputs processed in memory; no mission-history storage",
            "limitations": "No Meta reasoning, autonomous repairs or production integrations"}
