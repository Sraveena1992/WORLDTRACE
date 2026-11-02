"""Final candidate: REAL model evidence is optional, operator-protected and auditable.

Mock transport proves wiring and policy only; does not establish actual Meta access.
"""
from fastapi.testclient import TestClient
import app
from worldtrace import agent

client=TestClient(app.app)
TOKEN="private-judge-test-token"

def fake_model(goal, observations, checks):
    assert "supplier" in goal.lower()
    assert any(x["role"]=="source_csv" for x in observations)
    return {"summary":"Supplier A3 missing; manual approval recommended",
            "hypotheses":[{"claim":"Incomplete data transfer",
                           "evidence_roles":["source_csv"],"confidence":"medium"}],
            "next_action":"Seek approval for isolated database correction",
            "model":"META-CONTRACT-TEST-NOT-LIVE",
            "provider_response_id":"mock-provider-response",
            "provided_evidence":"Sanitized roles and counts"}

def test_model_assessment_requires_token_and_retains_event(monkeypatch):
    monkeypatch.setenv("WORLDTRACE_MISSION_TOKEN",TOKEN)
    monkeypatch.setattr(agent,"assess_uploaded_evidence",fake_model)
    created=client.post("/api/public-demo/start")
    assert created.status_code==201
    mid=created.json()["demo_id"]
    url=f"/api/public-demo/{mid}/meta-assess"
    assert client.post(url).status_code==403
    result=client.post(url,headers={"X-WORLDTRACE-TOKEN":TOKEN})
    assert result.status_code==200,result.text
    data=result.json()
    assert data["model_assessment"]["model"]=="META-CONTRACT-TEST-NOT-LIVE"
    assert data["model_assessment"]["provider_response_id"]=="mock-provider-response"
    assert any(e["role"]=="Meta Mission Commander" for e in data["trace"])
    assert data["trace_verified"] is True
    assert client.post(url,headers={"X-WORLDTRACE-TOKEN":TOKEN}).status_code==409
    # The AI is advisory; separate safety-approved execution still applies.
    assert client.post(f"/api/public-demo/{mid}/execute").status_code==409
    assert client.post(f"/api/public-demo/{mid}/approve").status_code==200
    after=client.post(f"/api/public-demo/{mid}/execute")
    assert after.status_code==200
    assert after.json()["verified"] is True
    assert after.json()["model_assessment"]["provider_response_id"]=="mock-provider-response"

def test_failed_provider_does_not_fake_success_or_lock_retry(monkeypatch):
    monkeypatch.setenv("WORLDTRACE_MISSION_TOKEN",TOKEN)
    mid=client.post("/api/public-demo/start").json()["demo_id"]
    def denied(*args):
        raise agent.ModelUnavailable("Provider HTTP 403. Organization access denied.")
    monkeypatch.setattr(agent,"assess_uploaded_evidence",denied)
    url=f"/api/public-demo/{mid}/meta-assess"
    error=client.post(url,headers={"X-WORLDTRACE-TOKEN":TOKEN})
    assert error.status_code==424
    current=client.get(f"/api/public-demo/{mid}").json()
    assert current["model_assessment"] is None
    assert not any(e["role"]=="Meta Mission Commander" for e in current["trace"])
    monkeypatch.setattr(agent,"assess_uploaded_evidence",fake_model)
    retry=client.post(url,headers={"X-WORLDTRACE-TOKEN":TOKEN})
    assert retry.status_code==200
    assert retry.json()["model_assessment"]["provider_response_id"]=="mock-provider-response"

def test_explicit_model_button_and_truthful_fallback():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    js=(root/"static/app.js").read_text(encoding="utf8")
    assert "/meta-assess" in js
    assert "if($('assessPublicMeta'))" in js
    assert "Real Meta inference NOT VERIFIED" in js
    assert "Meta Mission Commander" in js
    assert "id.startsWith('PUBLIC-DEMO-')" in js or "mission.id.startsWith('PUBLIC-DEMO-')" in js
