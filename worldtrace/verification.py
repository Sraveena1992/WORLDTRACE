"""Deterministic independent verification of local test evidence."""
def verify(tasks):
    counts = {key: sum(t["status"] == key for t in tasks) for key in ("passed", "finding", "error", "blocked")}
    checks = []
    by_tool = {t["tool"]: t for t in tasks}
    network, api = by_tool.get("network_inspect"), by_tool.get("api_virtualize")
    if network and api:
        statuses = {x.get("status") for x in network.get("result", {}).get("failures", [])}
        simulated = api.get("result", {}).get("simulated")
        checks.append({"id": "network_api_status_agreement", "pass": simulated in statuses, "basis": "HAR fixture versus local mock; NOT independent evidence of production outage"})
    etl, database = by_tool.get("etl_compare"), by_tool.get("database_check")
    if etl and database:
        missing = etl.get("result", {}).get("missing_ids", [])
        pending = database.get("result", {}).get("pending", 0)
        checks.append({"id": "data_pipeline_triage", "pass": not missing and pending == 0, "basis": "Synthetic CSV fixture and read-only sample SQL"})
    verdict = "needs-review" if (not tasks or counts["finding"] or counts["error"] or counts["blocked"] or any(not c["pass"] for c in checks)) else "verified-local-checks"
    return {"verdict": verdict, "counts": counts, "cross_checks": checks, "method": "deterministic tool assertions plus cross-tool checks on synthetic inputs", "limitations": "No independent AI judge, real production access, or physical-world proof"}
