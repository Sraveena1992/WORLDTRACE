"""v13 inference probe is explicit, token protected, and never misreports configuration as success."""
from fastapi.testclient import TestClient
import app

client=TestClient(app.app)

def test_model_probe_requires_private_token(monkeypatch):
    monkeypatch.setenv("WORLDTRACE_MISSION_TOKEN","test-secret")
    assert client.post("/api/model/probe").status_code==403

def test_model_probe_reports_absent_provider_as_unavailable(monkeypatch):
    monkeypatch.setenv("WORLDTRACE_MISSION_TOKEN","test-secret")
    monkeypatch.delenv("WORLDTRACE_MODEL_API_KEY",raising=False)
    monkeypatch.delenv("WORLDTRACE_MODEL_BASE_URL",raising=False)
    result=client.post("/api/model/probe",headers={"X-WORLDTRACE-TOKEN":"test-secret"})
    assert result.status_code==424
    assert "not configured" in result.json()["detail"].lower()

def test_model_probe_only_reports_actual_provider_success(monkeypatch):
    monkeypatch.setenv("WORLDTRACE_MISSION_TOKEN","test-secret")
    def fake_probe():
        return {"connected":True,"inference_verified":True,
                "requested_model":"test-verified-model","returned_model":"test-verified-model",
                "provider":"test","response_id":"r1","message":"Mock response in test only"}
    monkeypatch.setattr(app.agent,"probe_provider",fake_probe)
    out=client.post("/api/model/probe",headers={"X-WORLDTRACE-TOKEN":"test-secret"})
    assert out.status_code==200
    assert out.json()["inference_verified"] is True

def test_model_probe_ui_is_explicit():
    from pathlib import Path
    base=Path(__file__).resolve().parents[1]/"static"
    html=(base/"index.html").read_text(encoding="utf8")
    js=(base/"app.js").read_text(encoding="utf8")
    assert 'id="probeModel"' in html
    assert "may use credits" in html
    assert "$('probeModel').onclick" in js
    assert "fetch('/api/model/probe'" in js
    assert '/assets/app.js?v=22' in html
