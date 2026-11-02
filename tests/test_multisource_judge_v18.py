"""Judge-facing multi-source evidence test: more than a trivial CSV mismatch."""
from fastapi.testclient import TestClient
import app

client=TestClient(app.app)

def test_multi_source_incident_reports_real_cross_tool_evidence():
    started=client.post("/api/public-demo/start?scenario=multi_source_incident")
    assert started.status_code==201,started.text
    data=started.json()
    assert data["scenario"]=="multi_source_incident"
    assert set(data["evidence_roles"])=={"source_csv","har","api_json"}
    roles={x["role"]:x for x in data["observations"]}
    assert roles["source_csv"]["result"]["missing_ids"]==["A3"]
    assert roles["har"]["result"]["failure_count"]==1
    assert roles["har"]["result"]["failures"][0]["status"]==503
    assert roles["api_json"]["result"]["expected_status"]==200
    assert roles["api_json"]["result"]["simulated_status"]==503
    assert len(data["cross_checks"])==1
    assert data["cross_checks"][0]["matched"] is True
    assert data["trace_verified"] is True
    assert data["status"]=="REVIEW_NEEDED"
    mid=data["demo_id"]
    assert client.post(f"/api/public-demo/{mid}/execute").status_code==409
    assert client.post(f"/api/public-demo/{mid}/approve").status_code==200
    out=client.post(f"/api/public-demo/{mid}/execute")
    assert out.status_code==200,out.text
    result=out.json()
    assert result["status"]=="VERIFIED_SANDBOX"
    assert result["current_target_rows"]==3
    assert result["rows_added"]==1
    assert result["trace_verified"] is True
    assert result["external_writes"]==0
    # Correlated API failure is still present: only a synthetic DB copy was repaired.
    assert result["cross_checks"]==data["cross_checks"]

def test_multi_source_ui_explains_no_external_api_repair():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    html=(root/"static/index.html").read_text(encoding="utf8")
    js=(root/"static/app.js").read_text(encoding="utf8")
    assert 'id="startMultiSourceDemo"' in html
    assert "multi_source_incident" in js
    assert "does not resolve or repair the observed HTTP 503" in js
    assert "app.js?v=27" in html
