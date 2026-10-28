"""v13 explicit persistence, private retrieval, and human review tests."""
import hashlib
from fastapi.testclient import TestClient
import app

client=TestClient(app.app)
TOKEN="private-v13-tests-only"
HEADERS={"X-WORLDTRACE-TOKEN":TOKEN}
GOAL="Investigate the source and target mismatch, deliver verified evidence."
FILES={"source_csv":("source.csv",b"id,name\n1,Alpha\n2,Beta\n","text/csv"),
       "target_csv":("target.csv",b"id,name\n1,Alpha\n","text/csv")}

def test_explicit_opt_in_and_authenticated_history(monkeypatch,tmp_path):
    monkeypatch.setenv("WORLDTRACE_DATA_DIR",str(tmp_path))
    monkeypatch.setenv("WORLDTRACE_MISSION_TOKEN",TOKEN)
    transient=client.post("/api/multi-file-missions/run",headers=HEADERS,
        data={"goal":GOAL},files=FILES)
    assert transient.status_code==200,transient.text
    assert "saved_mission_id" not in transient.json()
    assert client.get("/api/unified-missions",headers=HEADERS).json()==[]
    saved=client.post("/api/multi-file-missions/run",headers=HEADERS,
        data={"goal":GOAL,"retain_result":"true"},files=FILES)
    assert saved.status_code==200,saved.text
    info=saved.json()
    mid=info["saved_mission_id"]
    assert mid.startswith("UM-")
    assert client.get("/api/unified-missions").status_code==403
    assert client.get("/api/unified-missions/"+mid).status_code==403
    listing=client.get("/api/unified-missions",headers=HEADERS).json()
    assert len(listing)==1 and listing[0]["id"]==mid
    loaded=client.get("/api/unified-missions/"+mid,headers=HEADERS).json()
    assert loaded["observations"][0]["result"]["missing_ids"]==["2"]
    assert hashlib.sha256(loaded["report_markdown"].encode()).hexdigest()==loaded["report_sha256"]
    assert loaded["decisions"]==[]

def test_manual_review_is_one_time_and_nonexecuting(monkeypatch,tmp_path):
    monkeypatch.setenv("WORLDTRACE_DATA_DIR",str(tmp_path))
    monkeypatch.setenv("WORLDTRACE_MISSION_TOKEN",TOKEN)
    saved=client.post("/api/multi-file-missions/run",headers=HEADERS,
        data={"goal":GOAL,"retain_result":"true"},files=FILES).json()
    mid=saved["saved_mission_id"]
    url="/api/unified-missions/"+mid+"/decisions"
    payload={"action_index":0,"decision":"approve_manual_followup",
             "reviewer":"Test Reviewer","note":"Investigate manually"}
    assert client.post(url,json=payload).status_code==403
    result=client.post(url,json=payload,headers=HEADERS)
    assert result.status_code==201,result.text
    assert result.json()["executed"] is False
    assert client.post(url,json=payload,headers=HEADERS).status_code==409
    detail=client.get("/api/unified-missions/"+mid,headers=HEADERS).json()
    assert len(detail["decisions"])==1
    assert detail["decisions"][0]["decision"]=="approve_manual_followup"

def test_ui_contains_real_persistence_controls():
    from pathlib import Path
    base=Path(__file__).resolve().parents[1]/"static"
    html=(base/"index.html").read_text(encoding="utf8")
    js=(base/"app.js").read_text(encoding="utf8")
    assert 'id="multiRetain"' in html
    assert 'id="unifiedHistory"' in html
    assert 'id="loadUnifiedReviews"' in html
    assert "body.append('retain_result'" in js
    assert "api('/api/unified-missions'" in js
    assert "approve_manual_followup" in js
    assert '/assets/app.js?v=15' in html
