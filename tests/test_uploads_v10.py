"""Real-file analysis: authenticated API, format limits, independent content."""
import csv
import io
import json
from fastapi.testclient import TestClient
import app
from worldtrace import uploads, samples, tools

client=TestClient(app.app)
TOKEN="test-only-token-for-upload-v10"
HEADERS={"X-WORLDTRACE-TOKEN":TOKEN}

def test_pdf_upload_uses_actual_bytes_not_fixture(monkeypatch):
    monkeypatch.setenv("WORLDTRACE_MISSION_TOKEN",TOKEN)
    samples.ensure()
    payload=tools.safe_path("supplier_check.pdf").read_bytes()
    assert client.post("/api/tools/pdf_inspect/inspect-upload",files={"file":("new.pdf",payload,"application/pdf")}).status_code==403
    response=client.post("/api/tools/pdf_inspect/inspect-upload",files={"file":("new.pdf",payload,"application/pdf")},headers=HEADERS)
    assert response.status_code==200,response.text
    result=response.json()
    assert result["source"]=="USER_UPLOADED_FILE"
    assert result["file_name"]=="new.pdf"
    assert result["result"]["pages"]>=1
    assert result["sha256"]

def test_etl_user_files_are_reconciled(monkeypatch):
    monkeypatch.setenv("WORLDTRACE_MISSION_TOKEN",TOKEN)
    source=b"id,name\nA1,Alpha\nA2,Beta\n"
    target=b"id,name\nA1,Alpha\n"
    response=client.post("/api/tools/etl_compare/inspect-upload",headers=HEADERS,
        files={"file":("source.csv",source,"text/csv"),"comparison":("target.csv",target,"text/csv")})
    assert response.status_code==200,response.text
    result=response.json()["result"]
    assert result["missing_ids"]==["A2"]
    assert result["source_rows"]==2 and result["target_rows"]==1

def test_har_and_message_validation(monkeypatch):
    monkeypatch.setenv("WORLDTRACE_MISSION_TOKEN",TOKEN)
    har={"log":{"entries":[{"request":{"url":"https://example.invalid/api"},"response":{"status":503}}]}}
    res=client.post("/api/tools/network_inspect/inspect-upload",headers=HEADERS,
        files={"file":("test.har",json.dumps(har).encode(),"application/json")})
    assert res.status_code==200,res.text
    assert res.json()["result"]["failure_count"]==1
    msgs=client.post("/api/tools/middleware_test/inspect-upload",headers=HEADERS,
        files={"file":("messages.json",b'[{"id":"one"},{"id":"one"}]',"application/json")})
    assert msgs.status_code==200 and msgs.json()["result"]["duplicates"]==["one"]

def test_reject_wrong_type_oversize_and_unknown(monkeypatch):
    monkeypatch.setenv("WORLDTRACE_MISSION_TOKEN",TOKEN)
    assert client.post("/api/tools/pdf_inspect/inspect-upload",headers=HEADERS,files={"file":("malware.exe",b"hello")}).status_code==422
    assert client.post("/api/tools/pdf_inspect/inspect-upload",headers=HEADERS,files={"file":("bad.pdf",b"x"*(uploads.MAX_BYTES+1))}).status_code==422
    assert client.post("/api/tools/database_check/inspect-upload",headers=HEADERS,files={"file":("db.sqlite",b"x")}).status_code==404
    assert client.post("/api/tools/etl_compare/inspect-upload",headers=HEADERS,files={"file":("source.csv",b"id\nA")}).status_code==422

def test_upload_ui_is_wired():
    from pathlib import Path
    static=Path(__file__).resolve().parents[1]/"static"
    html=(static/"index.html").read_text(encoding="utf-8")
    js=(static/"app.js").read_text(encoding="utf-8")
    assert 'id="uploadMain"' in html and 'id="analyzeUpload"' in html
    assert 'id="uploadComparison"' in html
    assert "'/inspect-upload'" in js
    assert "'X-WORLDTRACE-TOKEN':token" in js
    assert "USER FILE ANALYSIS" in js
