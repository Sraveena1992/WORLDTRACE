"""v11: one private instruction over multiple actual uploaded inputs."""
import json
import hashlib
from fastapi.testclient import TestClient
import app
from worldtrace import multifile

client=TestClient(app.app)
TOKEN="test-only-private-multi-file-token"
HEADER={"X-WORLDTRACE-TOKEN":TOKEN}

def test_real_csv_har_api_correlated_and_report_verified(monkeypatch):
    monkeypatch.setenv("WORLDTRACE_MISSION_TOKEN",TOKEN)
    files={
        "source_csv":("source.csv",b"id,name\nA1,Alpha\nA2,Beta\n"),
        "target_csv":("target.csv",b"id,name\nA1,Alpha\n"),
        "har":("network.har",json.dumps({"log":{"entries":[{"request":{"url":"https://example.invalid/api"},"response":{"status":503}}]}}).encode()),
        "api_json":("api.json",json.dumps({"expected_status":200,"simulated_status":503}).encode())
    }
    goal="Investigate these supplier onboarding failures and deliver one evidence report"
    out=multifile.run(goal,files)
    assert out["mode"]=="deterministic_multi_file"
    assert out["status"]=="REVIEW_NEEDED"
    assert len(out["observations"])==3
    assert out["cross_checks"][0]["matched"] is True
    assert "A2" in out["report_markdown"]
    assert hashlib.sha256(out["report_markdown"].encode()).hexdigest()==out["report_sha256"]
    assert out["trace"][0]["prev_hash"]=="GENESIS"
    assert all(out["trace"][i]["prev_hash"]==out["trace"][i-1]["hash"] for i in range(1,len(out["trace"])))
    assert all(not a["executed"] for a in out["proposed_actions"])

def test_authenticated_multi_file_endpoint(monkeypatch):
    monkeypatch.setenv("WORLDTRACE_MISSION_TOKEN",TOKEN)
    request={"goal":"Investigate and report the supplied data quality issue"}
    files={"source_csv":("source.csv",b"id,name\nA1,X\nA2,Y\n","text/csv"),
           "target_csv":("target.csv",b"id,name\nA1,X\n","text/csv")}
    assert client.post("/api/multi-file-missions/run",data=request,files=files).status_code==403
    response=client.post("/api/multi-file-missions/run",data=request,files=files,headers=HEADER)
    assert response.status_code==200,response.text
    data=response.json()
    assert data["observations"][0]["result"]["missing_ids"]==["A2"]
    assert "Multi-File Evidence Report" in data["report_markdown"]

def test_missing_etl_target_rejected(monkeypatch):
    monkeypatch.setenv("WORLDTRACE_MISSION_TOKEN",TOKEN)
    result=client.post("/api/multi-file-missions/run",headers=HEADER,
        data={"goal":"Investigate this uploaded CSV dataset"},
        files={"source_csv":("source.csv",b"id,name\nA1,X\n")})
    assert result.status_code==422
    assert "both" in result.text.lower()

def test_no_input_or_oversize_rejected(monkeypatch):
    monkeypatch.setenv("WORLDTRACE_MISSION_TOKEN",TOKEN)
    goal={"goal":"Investigate real uploaded evidence and report"}
    assert client.post("/api/multi-file-missions/run",data=goal,headers=HEADER).status_code==422
    assert client.post("/api/multi-file-missions/run",data=goal,headers=HEADER,
        files={"pdf":("file.pdf",b"x"*(2*1024*1024+1))}).status_code==422

def test_frontend_multi_file_controls_exist():
    from pathlib import Path
    base=Path(__file__).resolve().parents[1]/"static"
    html=(base/"index.html").read_text(encoding="utf8")
    js=(base/"app.js").read_text(encoding="utf8")
    assert 'data-route="multi"' in html
    assert 'id="multi" class="page"' in html
    assert 'id="multiRun"' in html
    assert "fetch('/api/multi-file-missions/run'" in js
    assert "data.report_markdown" in js
