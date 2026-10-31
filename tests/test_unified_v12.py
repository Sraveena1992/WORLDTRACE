"""v12 unified mission acceptance and distinct agent responsibility checks."""
from pathlib import Path
from fastapi.testclient import TestClient
import app
from worldtrace import multifile
BASE=Path(__file__).resolve().parents[1]/"static"
HTML=(BASE/"index.html").read_text(encoding="utf8")
JS=(BASE/"app.js").read_text(encoding="utf8")
client=TestClient(app.app)
HEADER={"X-WORLDTRACE-TOKEN":"private-v12-test-token"}

def test_primary_mission_entry_and_distinct_agents():
    assert 'id="openUnifiedMission"' in HTML
    assert "$('focusGoal').onclick=()=>route('multi')" in JS
    assert 'id="agentMissionSelect"' in HTML
    assert 'data-route="multi"' not in HTML  # merged into Mission Control
    assert "function renderAgentWorkforce()" in JS
    assert "app.unifiedMissions.unshift(mission)" in JS
    assert "data-launch-tool=" in JS # tools remain available, not copied into agents
    assert "$('agentGrid').innerHTML=RESPONSIBILITIES.map" in JS
    assert "agent.followup_decision" not in HTML  # no invented AI model trace

def test_six_roles_use_actual_uploaded_file_trace(monkeypatch):
    monkeypatch.setenv("WORLDTRACE_MISSION_TOKEN","private-v12-test-token")
    response=client.post("/api/multi-file-missions/run",
        data={"goal":"Inspect uploaded business files, verify differences, and deliver findings"},
        headers=HEADER,
        files={"source_csv":("source.csv",b"id,name\n1,Alpha\n2,Beta\n","text/csv"),
               "target_csv":("target.csv",b"id,name\n1,Alpha\n","text/csv")})
    assert response.status_code==200,response.text
    result=response.json()
    roles={e["role"] for e in result["trace"]}
    assert roles=={"Research Agent","Security Agent","Execution Agent","Verification Agent","Builder Agent","Delivery Agent"}
    assert result["observations"][0]["result"]["missing_ids"]==["2"]
    assert result["mode"]=="deterministic_multi_file"
    assert result["status"]=="REVIEW_NEEDED"
    assert "2" in result["report_markdown"]
    assert all(not a["executed"] for a in result["proposed_actions"])

def test_navigation_and_reporting_wired():
    assert "function renderAgentWorkforce()" in JS
    assert "$('agentMissionSelect').onchange" in JS
    assert "route('agents')" in JS
    assert "data.report_markdown" in JS
    assert "id=\"downloadMulti\"" in JS
    assert '/assets/app.js?v=21' in HTML
