"""Browser review controls must be wired to protected API and require human intent."""
from pathlib import Path
JS=(Path(__file__).resolve().parents[1]/"static"/"app.js").read_text(encoding="utf-8")

def test_review_controls_are_interactive():
    assert 'data-review-decision="approve_for_manual_followup"' in JS
    assert 'data-review-decision="reject"' in JS
    assert "button.onclick=()=>submitRecoveryReview" in JS

def test_review_request_uses_private_token():
    assert "'X-WORLDTRACE-TOKEN':token" in JS
    assert "reviewer:reviewer.trim()" in JS
    assert "No repairs were executed." in JS
