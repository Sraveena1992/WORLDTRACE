"""End-to-end approved sandbox demo: no external writes, real SQLite after-check."""
import hashlib
import json
from fastapi.testclient import TestClient
import app

TOKEN="demo-recovery-private-token"
HEAD={"X-WORLDTRACE-TOKEN":TOKEN}
GOAL="Investigate missing supplier onboarding rows and apply a controlled approved correction"
FILES={"source_csv":("source.csv",b"id,name\nA1,Alpha\nA2,Beta\nA3,Gamma\n","text/csv"),
       "target_csv":("target.csv",b"id,name\nA1,Alpha\nA2,Beta\n","text/csv")}
client=TestClient(app.app)

def setup_demo(monkeypatch,tmp_path,files=FILES):
    monkeypatch.setenv("WORLDTRACE_DATA_DIR",str(tmp_path))
    monkeypatch.setenv("WORLDTRACE_MISSION_TOKEN",TOKEN)
    response=client.post("/api/multi-file-missions/run",headers=HEAD,
        data={"goal":GOAL,"retain_result":"true"},files=files)
    assert response.status_code==200,response.text
    result=response.json()
    assert result["saved_mission_id"]
    assert result["demo_repair"]["missing_record_count"]>0
    assert result["proposed_actions"][0]["type"]=="sandbox_csv_reconcile"
    return result["saved_mission_id"]

def test_approve_execute_verify_exact_difference(monkeypatch,tmp_path):
    mid=setup_demo(monkeypatch,tmp_path)
    execute=f"/api/unified-missions/{mid}/execute-demo-correction"
    body={"action_index":0}
    assert client.post(execute,json=body).status_code==403
    assert client.post(execute,json=body,headers=HEAD).status_code==409
    approve=client.post(f"/api/unified-missions/{mid}/decisions",headers=HEAD,
       json={"action_index":0,"decision":"approve_manual_followup",
             "reviewer":"Demo Reviewer"})
    assert approve.status_code==201,approve.text
    done=client.post(execute,json=body,headers=HEAD)
    assert done.status_code==201,done.text
    info=done.json()
    assert info["execution"]=="ISOLATED_SQLITE_SANDBOX_ONLY"
    assert info["executed"] is True and info["verified"] is True
    assert info["before_count"]==2 and info["after_count"]==3
    assert info["rows_added"]==1 and info["external_writes"]==0
    assert info["original_csv_modified"] is False
    assert info["before_sha256"]!=info["after_sha256"]
    assert client.post(execute,json=body,headers=HEAD).status_code==409
    detail=client.get(f"/api/unified-missions/{mid}",headers=HEAD).json()
    assert detail["sandbox_executions"][0]["verified"]==1

def test_rejected_correction_never_executes(monkeypatch,tmp_path):
    mid=setup_demo(monkeypatch,tmp_path)
    result=client.post(f"/api/unified-missions/{mid}/decisions",headers=HEAD,
       json={"action_index":0,"decision":"reject","reviewer":"Demo Reviewer"})
    assert result.status_code==201
    assert client.post(f"/api/unified-missions/{mid}/execute-demo-correction",
       headers=HEAD,json={"action_index":0}).status_code==409

def test_extra_or_mismatch_rows_refuse_repair(monkeypatch,tmp_path):
    files={
       "source_csv":("source.csv",b"id,name\nA1,Alpha\nA2,Beta\nA3,Gamma\n","text/csv"),
       "target_csv":("target.csv",b"id,name\nA1,Wrong\n","text/csv")}
    mid=setup_demo(monkeypatch,tmp_path,files)
    client.post(f"/api/unified-missions/{mid}/decisions",headers=HEAD,
       json={"action_index":0,"decision":"approve_manual_followup","reviewer":"Demo Reviewer"})
    result=client.post(f"/api/unified-missions/{mid}/execute-demo-correction",
       headers=HEAD,json={"action_index":0})
    assert result.status_code==409
    assert "separate intervention" in result.json()["detail"]

def test_ui_has_explicit_execution_and_before_after_evidence():
    from pathlib import Path
    base=Path(__file__).resolve().parents[1]/"static"
    js=(base/"app.js").read_text(encoding="utf8")
    assert "data-execute-demo" in js
    assert "execute-demo-correction" in js
    assert "ACTUAL SANDBOX EXECUTION VERIFIED" in js
