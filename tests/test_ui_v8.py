"""Outcome Studio front-end must create and deliver actual backend files."""
from pathlib import Path
HTML=(Path(__file__).resolve().parents[1]/"static"/"index.html").read_text(encoding="utf-8")
JS=(Path(__file__).resolve().parents[1]/"static"/"app.js").read_text(encoding="utf-8")

def test_outcome_studio_has_real_request_inputs_and_route():
    for marker in ('data-route="deliverables"', 'id="deliverables" class="page"', 'id="outcomeDomain"', 'id="outcomeGoal"', 'id="outcomeEvidence"', 'id="buildDeliverable"'):
        assert marker in HTML

def test_outcome_request_uses_authenticated_backend_and_real_download():
    assert "api('/api/deliverables',{method:'POST'" in JS
    assert "'X-WORLDTRACE-TOKEN':token" in JS
    assert "downloadPrivatePackage(data.download_url,data.id,token)" in JS
    assert "/assets/app.js?v=8" in HTML
