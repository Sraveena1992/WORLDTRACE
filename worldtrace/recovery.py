"""Bounded remediation guidance grounded in observed fixture results.

Never performs remediation, sends messages, or modifies an external system.
"""
RULES = {
    "pdf_inspect": ("Request a signed supplier document and re-run document checks.", "Document owner"),
    "email_inspect": ("Review the supplier notice for the required onboarding and missing-evidence language.", "Communications owner"),
    "network_inspect": ("Investigate recorded HTTP failures against authorized service logs before considering remediation.", "API operations owner"),
    "etl_compare": ("Reconcile missing and mismatched records in a reviewed ETL change; re-run comparison.", "Data engineering owner"),
    "database_check": ("Review pending sample supplier records against onboarding criteria; do not auto-approve.", "Compliance owner"),
    "api_virtualize": ("Resolve the mocked API contract/status mismatch and re-run contract tests.", "API engineering owner"),
    "performance_probe": ("Re-run the bounded performance probe; benchmark is not production load evidence.", "Performance owner"),
    "middleware_test": ("Review duplicate message IDs and idempotency rules before replaying anything.", "Integration owner"),
    "mainframe_contract": ("Correct invalid fixed-width record formatting in an approved test fixture.", "Legacy systems owner"),
}

def recommend(tasks):
    """Return actionable human-review suggestions without pretending to repair anything."""
    results = []
    for task in tasks:
        status = task.get("status")
        if status not in ("finding", "error", "blocked"):
            continue
        tool = task.get("tool", "")
        action, owner = RULES.get(tool, ("Investigate the reported tool result manually.", "Mission owner"))
        results.append({
            "tool": tool,
            "status": status,
            "owner": owner,
            "proposed_action": action,
            "execution": "NOT EXECUTED - human approval and independent verification required",
            "basis": "Synthetic fixture tool result",
        })
    return results
