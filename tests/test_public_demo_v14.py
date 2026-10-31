"""Synthetic public demo acceptance: zero secrets and no production effects."""
from fastapi.testclient import TestClient
import app

client=TestClient(app.app)

def test_public_demo_requires_separate_approval_and_reverifies_sqlite():
    started=client.post("/api/public-demo/start")
    assert started.status_code==201,started.text
    data=started.json()
    mid=data["demo_id"]
    assert data["requires_private_token"] is False
    assert data["status"]=="REVIEW_NEEDED"
    assert data["source_rows"]==3 and data["initial_target_rows"]==2
    assert data["missing_ids"]==["A3"]
    assert data["trace_verified"] is True
    assert client.post(f"/api/public-demo/{mid}/execute").status_code==409
    accepted=client.post(f"/api/public-demo/{mid}/approve")
    assert accepted.status_code==200,accepted.text
    assert accepted.json()["approved"] is True
    assert client.post(f"/api/public-demo/{mid}/approve").status_code==409
    result=client.post(f"/api/public-demo/{mid}/execute")
    assert result.status_code==200,result.text
    detail=result.json()
    assert detail["status"]=="VERIFIED_SANDBOX"
    assert detail["verified"] is True
    assert detail["current_target_rows"]==3
    assert detail["rows_added"]==1
    assert detail["before_sha256"]!=detail["after_sha256"]
    assert detail["external_writes"]==0
    assert detail["original_csv_modified"] is False
    assert detail["trace_verified"] is True
    assert client.post(f"/api/public-demo/{mid}/execute").status_code==409
    restored=client.get(f"/api/public-demo/{mid}")
    assert restored.status_code==200
    assert restored.json()["current_target_rows"]==3

def test_public_demo_invalid_token_rejected():
    assert client.get("/api/public-demo/not-a-real-id").status_code==404
    assert client.post("/api/public-demo/not-a-real-id/approve").status_code==404

def test_public_browser_interactions_are_real():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    js=(root/"static/app.js").read_text(encoding="utf-8")
    html=(root/"static/index.html").read_text(encoding="utf-8")
    for snippet in ("'/api/public-demo/start'", "'/approve'", "'/execute'",
                    "function renderPublicGuidedDemo(", "downloadPublicReceipt"):
        assert snippet in js
    assert 'id="startPublicDemo"' in html
    assert 'id="publicDemoOutput"' in html
    assert '/assets/app.js?v=24' in html
