"""Model missions require a server-side secret, unlike local demo missions."""
from fastapi.testclient import TestClient
import app

client = TestClient(app.app)

def test_model_disabled_without_token(monkeypatch):
    monkeypatch.delenv("WORLDTRACE_MISSION_TOKEN", raising=False)
    res = client.post("/api/missions", json={"goal": "Investigate synthetic supplier records", "mode": "model"})
    assert res.status_code == 503

def test_model_rejects_missing_or_wrong_token(monkeypatch):
    monkeypatch.setenv("WORLDTRACE_MISSION_TOKEN", "demo-secret-do-not-use")
    body = {"goal": "Investigate synthetic supplier records", "mode": "model"}
    assert client.post("/api/missions", json=body).status_code == 403
    assert client.post("/api/missions", json=body, headers={"X-WORLDTRACE-TOKEN": "wrong"}).status_code == 403

def test_model_accepts_matching_token(monkeypatch):
    monkeypatch.setenv("WORLDTRACE_MISSION_TOKEN", "demo-secret-do-not-use")
    monkeypatch.setattr(app.engine, "start", lambda goal, mode: "WT-TEST")
    res = client.post("/api/missions", json={"goal": "Investigate synthetic supplier records", "mode": "model"}, headers={"X-WORLDTRACE-TOKEN": "demo-secret-do-not-use"})
    assert res.status_code == 202
    assert res.json()["id"] == "WT-TEST"
