"""Adversarial judge test: approved does NOT mean unsafe execution is permitted."""
from fastapi.testclient import TestClient
import app

client=TestClient(app.app)

def test_conflicting_supplier_record_blocks_even_after_human_approval():
    opened=client.post("/api/public-demo/start?scenario=conflicting_record")
    assert opened.status_code==201,opened.text
    first=opened.json()
    assert first["scenario"]=="conflicting_record"
    assert first["source_rows"]==3
    assert first["initial_target_rows"]==2
    assert first["status"]=="REVIEW_NEEDED"
    ref=first["demo_id"]
    assert client.post(f"/api/public-demo/{ref}/execute").status_code==409
    approved=client.post(f"/api/public-demo/{ref}/approve")
    assert approved.status_code==200
    assert approved.json()["approved"] is True
    rejected=client.post(f"/api/public-demo/{ref}/execute")
    assert rejected.status_code==200,rejected.text
    data=rejected.json()
    assert data["status"]=="BLOCKED_UNSAFE_CONFLICT"
    assert data["verified"] is False
    assert data["block_reason"] and "differs" in data["block_reason"]
    assert data["current_target_rows"]==2
    assert data["rows_added"]==0
    assert data["after_sha256"] is None
    assert data["external_writes"]==0
    assert data["original_csv_modified"] is False
    assert data["trace_verified"] is True
    assert any(e["action"]=="reject_unsafe_correction" for e in data["trace"])
    assert client.post(f"/api/public-demo/{ref}/execute").status_code==409
    reopened=client.get(f"/api/public-demo/{ref}")
    assert reopened.status_code==200
    assert reopened.json()["current_target_rows"]==2

def test_public_demo_rejects_unsupported_scenario():
    response=client.post("/api/public-demo/start?scenario=production_db")
    assert response.status_code==422

def test_adversarial_demo_has_live_ui_and_safe_report():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    html=(root/"static/index.html").read_text(encoding="utf8")
    js=(root/"static/app.js").read_text(encoding="utf8")
    assert 'id="startPublicChallenge"' in html
    assert "scenario=conflicting_record" in js
    assert "BLOCKED_UNSAFE_CONFLICT" in js
    assert "downloadBlockedReceipt" in js
    assert '/assets/app.js?v=27' in html
