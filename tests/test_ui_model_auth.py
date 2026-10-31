"""Regression checks for browser-to-API model authorization integration."""
from pathlib import Path

JS = (Path(__file__).resolve().parents[1] / "static" / "app.js").read_text(encoding="utf-8")

def test_model_mode_sends_private_mission_header():
    assert "headers['X-WORLDTRACE-TOKEN']=token" in JS
    assert "const token=privateToken()" in JS
    assert "app.mode==='model'" in JS

def test_private_mission_token_not_persisted_in_browser_storage():
    assert "localStorage" not in JS
    assert "sessionStorage" not in JS
    assert "missionToken:null" in JS

def test_dashboard_does_not_falsely_claim_inference_ready():
    assert 'READY<span class="metric-unit">API</span>' not in JS
    assert "Credentials configured; inference NOT yet verified" in JS
