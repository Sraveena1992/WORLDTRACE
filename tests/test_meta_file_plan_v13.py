"""v13 model role planning must be real, allowlisted, and explicitly requested."""
from fastapi.testclient import TestClient
from worldtrace import multifile,agent
import app

client=TestClient(app.app)
TOKEN="v13-planning-test-token"
HEAD={"X-WORLDTRACE-TOKEN":TOKEN}
FILES={"source_csv":("source.csv",b"id,name\nA1,A\nA2,B\n"),
       "target_csv":("target.csv",b"id,name\nA1,A\n")}

def test_model_plan_is_rejected_if_roles_change():
    try:
        multifile.run("Investigate these two uploaded CSV files",FILES,
                     model_plan={"ordered_roles":["source_csv"],"reason":"bad"})
    except ValueError as exc:
        assert "exactly" in str(exc)
    else:
        raise AssertionError("Incomplete model plan was accepted")

def test_explicit_model_plan_requires_live_provider(monkeypatch,tmp_path):
    monkeypatch.setenv("WORLDTRACE_DATA_DIR",str(tmp_path))
    monkeypatch.setenv("WORLDTRACE_MISSION_TOKEN",TOKEN)
    monkeypatch.delenv("WORLDTRACE_MODEL_API_KEY",raising=False)
    monkeypatch.delenv("WORLDTRACE_MODEL_BASE_URL",raising=False)
    response=client.post("/api/multi-file-missions/run",data={
        "goal":"Investigate uploaded CSV and propose safe processing order",
        "model_planning":"true"},files=FILES,headers=HEAD)
    assert response.status_code==424
    assert "not configured" in response.json()["detail"]

def test_mocked_provider_plan_provenance(monkeypatch,tmp_path):
    monkeypatch.setenv("WORLDTRACE_DATA_DIR",str(tmp_path))
    monkeypatch.setenv("WORLDTRACE_MISSION_TOKEN",TOKEN)
    def plan(goal,roles):
        assert set(roles)=={"source_csv","target_csv"}
        return {"ordered_roles":["target_csv","source_csv"],"reason":"inspect both files safely",
                "model":"TEST-MODEL-MOCK","provider_response_id":"test-only-id"}
    monkeypatch.setattr(agent,"make_uploaded_file_plan",plan)
    monkeypatch.setattr(agent,"assess_uploaded_evidence",lambda goal,obs,checks: {"summary":"Missing record detected","hypotheses":[{"claim":"Source and target differ","evidence_roles":["source_csv"],"confidence":"high"}],"next_action":"Request review","model":"TEST-MODEL-MOCK","provider_response_id":"second-mock-id"})
    response=client.post("/api/multi-file-missions/run",data={
        "goal":"Investigate uploaded CSV and propose safe processing order",
        "model_planning":"true"},files=FILES,headers=HEAD)
    assert response.status_code==200,response.text
    result=response.json()
    assert result["mode"]=="meta_planned_multi_file"
    assert result["trace"][0]["role"]=="Mission Commander"
    assert result["model_plan"]["model"]=="TEST-MODEL-MOCK"
    assert result["model_assessment"]["summary"]=="Missing record detected"
    assert any(e["action"]=="meta_model_evidence_assessment" for e in result["trace"])
    assert result["observations"][0]["result"]["missing_ids"]==["A2"]

def test_opt_in_model_ui():
    from pathlib import Path
    path=Path(__file__).resolve().parents[1]/"static"
    html=(path/"index.html").read_text(encoding="utf8")
    js=(path/"app.js").read_text(encoding="utf8")
    assert 'id="multiModel"' in html
    assert "body.append('model_planning'" in js
    assert 'app.js?v=23' in html
