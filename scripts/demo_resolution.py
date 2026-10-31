"""One-command, zero-cost WORLDTRACE supplier-resolution acceptance run.

Usage (repo root): python scripts/demo_resolution.py
No Meta inference; no production data; no external network or writes.
"""
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from fastapi.testclient import TestClient
import app

def main():
    with TemporaryDirectory(prefix="worldtrace_demo_") as workdir:
        os.environ["WORLDTRACE_DATA_DIR"]=workdir
        os.environ["WORLDTRACE_MISSION_TOKEN"]="worldtrace-demo-local-only-operator-token"
        token={"X-WORLDTRACE-TOKEN":os.environ["WORLDTRACE_MISSION_TOKEN"]}
        client=TestClient(app.app)
        goal="Investigate missing supplier onboarding data, request approval, apply a bounded sandbox correction, and independently verify the result."
        files={
            "source_csv":("supplier-source.csv",b"id,name\nA1,Alpha\nA2,Beta\nA3,Gamma\n","text/csv"),
            "target_csv":("supplier-target.csv",b"id,name\nA1,Alpha\nA2,Beta\n","text/csv")}
        response=client.post("/api/multi-file-missions/run",headers=token,
            data={"goal":goal,"retain_result":"true","model_planning":"false"},files=files)
        response.raise_for_status()
        mission=response.json()
        mid=mission["saved_mission_id"]
        assert mission["status"]=="REVIEW_NEEDED"
        assert mission["observations"][0]["result"]["missing_ids"]==["A3"]
        assert mission["proposed_actions"][0]["type"]=="sandbox_csv_reconcile"
        attempted=client.post(f"/api/unified-missions/{mid}/execute-demo-correction",
             headers=token,json={"action_index":0})
        assert attempted.status_code==409,"Unapproved correction was incorrectly allowed"
        approved=client.post(f"/api/unified-missions/{mid}/decisions",headers=token,
            json={"action_index":0,"decision":"approve_manual_followup",
                  "reviewer":"Local Demo Reviewer","note":"Authorized isolated sandbox only"})
        approved.raise_for_status()
        executed=client.post(f"/api/unified-missions/{mid}/execute-demo-correction",
            headers=token,json={"action_index":0})
        executed.raise_for_status()
        detail=client.get(f"/api/unified-missions/{mid}",headers=token)
        detail.raise_for_status()
        after=detail.json()
        result=executed.json()
        assert result["verified"] is True
        assert result["before_count"]==2 and result["after_count"]==3
        assert result["rows_added"]==1
        assert result["external_writes"]==0
        assert after["trace_verified"] is True and after["report_verified"] is True
        second=client.post(f"/api/unified-missions/{mid}/execute-demo-correction",
             headers=token,json={"action_index":0})
        assert second.status_code==409,"Duplicate correction was incorrectly allowed"
        print(json.dumps({
            "result":"PASS: APPROVED SANDBOX CORRECTION VERIFIED",
            "mission":mid,"missing_supplier_ids":["A3"],
            "human_approval_recorded":True,"unauthorized_execution_blocked":True,
            "before_target_rows":result["before_count"],
            "after_target_rows":result["after_count"],
            "sandbox_records_added":result["rows_added"],
            "trace_hashes_verified":after["trace_verified"],
            "report_sha256_verified":after["report_verified"],
            "duplicate_replay_blocked":True,
            "production_records_modified":False,
            "model_inference_used":False
        },indent=2))

if __name__=="__main__":
    main()
