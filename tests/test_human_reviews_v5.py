"""Review decisions are authorized, one-time and never execute recovery."""
import time
from fastapi.testclient import TestClient
import app
from worldtrace import samples, storage

client = TestClient(app.app)
TOKEN = "synthetic-testing-token"

def finished_mission():
    samples.ensure()
    body = {"goal": "Investigate supplier onboarding failures and produce evidence", "mode": "local"}
    r = client.post("/api/missions", json=body)
    assert r.status_code == 202
    mid = r.json()["id"]
    for _ in range(120):
        m = storage.get(mid)
        if m["status"] in ("completed", "error"):
            break
        time.sleep(.05)
    assert m["status"] == "completed"
    return mid

def test_review_requires_private_token(monkeypatch):
    monkeypatch.setenv("WORLDTRACE_MISSION_TOKEN", TOKEN)
    mid = finished_mission()
    body = {"tool": "pdf_inspect", "decision": "reject", "reviewer": "Test reviewer"}
    assert client.post(f"/api/missions/{mid}/reviews", json=body).status_code == 403
    assert client.get(f"/api/missions/{mid}/reviews").status_code == 403

def test_recovery_manual_review_is_audited_and_one_time(monkeypatch):
    monkeypatch.setenv("WORLDTRACE_MISSION_TOKEN", TOKEN)
    mid = finished_mission()
    url = f"/api/missions/{mid}/reviews"
    headers = {"X-WORLDTRACE-TOKEN": TOKEN}
    body = {"tool": "pdf_inspect", "decision": "approve_for_manual_followup", "reviewer": "Demo operator", "note": "Review document only"}
    res = client.post(url, json=body, headers=headers)
    assert res.status_code == 201, res.text
    assert res.json()["executed"] is False
    assert client.post(url,json=body,headers=headers).status_code == 409
    assert client.post(url,json={**body,"tool":"email_inspect"},headers=headers).status_code == 409
    assert client.post(url,json={**body,"decision":"execute"},headers=headers).status_code == 422
    assert len(client.get(url,headers=headers).json()) == 1
    assert storage.verify_chain(mid)
    assert any(e["kind"] == "recovery.reviewed" and e["payload"]["executed"] is False for e in storage.get(mid)["events"])
