"""WORLDTRACE public judge benchmark: repeatable, no secrets, no Meta inference.

Run from repository root:
    python scripts/judge_benchmark.py

Runs controlled successful correction and adversarial refusal against the actual
FastAPI route handlers via TestClient. This does NOT benchmark Meta inference,
production integrations or independent customer impact.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
import app


def evaluate():
    checks = {}
    with TestClient(app.app) as client:
        good = client.post("/api/public-demo/start")
        assert good.status_code == 201, good.text
        initial = good.json()
        mid = initial["demo_id"]
        checks["supplier_discrepancy_detected"] = (
            initial["missing_ids"] == ["A3"]
            and initial["source_rows"] == 3
            and initial["initial_target_rows"] == 2
            and initial["trace_verified"] is True
        )
        checks["unauthorized_execution_denied"] = (
            client.post(f"/api/public-demo/{mid}/execute").status_code == 409
        )
        approved = client.post(f"/api/public-demo/{mid}/approve")
        checks["explicit_human_approval_recorded"] = (
            approved.status_code == 200 and approved.json()["approved"] is True
        )
        verified = client.post(f"/api/public-demo/{mid}/execute")
        assert verified.status_code == 200, verified.text
        actual = verified.json()
        checks["approved_correction_verified"] = (
            actual["status"] == "VERIFIED_SANDBOX"
            and actual["current_target_rows"] == 3
            and actual["rows_added"] == 1
            and actual["before_sha256"] != actual["after_sha256"]
            and actual["trace_verified"] is True
            and actual["external_writes"] == 0
        )
        checks["replay_denied"] = (
            client.post(f"/api/public-demo/{mid}/execute").status_code == 409
        )

        challenge = client.post("/api/public-demo/start?scenario=conflicting_record")
        assert challenge.status_code == 201, challenge.text
        challenge_id = challenge.json()["demo_id"]
        checks["conflict_requires_human_review"] = (
            challenge.json()["status"] == "REVIEW_NEEDED"
        )
        checks["conflict_preapproval_execution_denied"] = (
            client.post(f"/api/public-demo/{challenge_id}/execute").status_code == 409
        )
        assert client.post(f"/api/public-demo/{challenge_id}/approve").status_code == 200
        blocked = client.post(f"/api/public-demo/{challenge_id}/execute")
        assert blocked.status_code == 200, blocked.text
        refused = blocked.json()
        checks["unsafe_approved_change_blocked"] = (
            refused["status"] == "BLOCKED_UNSAFE_CONFLICT"
            and refused["approved"] is True
            and refused["verified"] is False
            and refused["rows_added"] == 0
            and refused["initial_target_rows"] == refused["current_target_rows"] == 2
            and refused["external_writes"] == 0
        )
        checks["refusal_evidence_chain_verified"] = (
            refused["trace_verified"] is True
            and any(event["action"] == "reject_unsafe_correction" for event in refused["trace"])
        )
        checks["blocked_action_replay_denied"] = (
            client.post(f"/api/public-demo/{challenge_id}/execute").status_code == 409
        )
        checks["invalid_scenario_denied"] = (
            client.post("/api/public-demo/start?scenario=external_production").status_code == 422
        )
        checks["unrecognized_session_denied"] = (
            client.get("/api/public-demo/not-a-real-token").status_code == 404
        )

    passed = sum(value is True for value in checks.values())
    summary = {
        "project": "WORLDTRACE",
        "evaluation": "deterministic-synthetic-public-demo-v1",
        "result": "PASS" if passed == len(checks) else "FAIL",
        "checks_passed": passed,
        "checks_total": len(checks),
        "checks": checks,
        "sample_size": "2 fixed synthetic scenarios; not production workload",
        "meta_inference_used": False,
        "external_systems_modified": False,
        "claims_excluded": [
            "real Meta model quality or API access",
            "live production integrations",
            "production-grade authorization or storage",
            "independent real-customer impact",
        ],
    }
    return summary


if __name__ == "__main__":
    output = evaluate()
    print(json.dumps(output, indent=2))
    if output["result"] != "PASS":
        sys.exit(1)
