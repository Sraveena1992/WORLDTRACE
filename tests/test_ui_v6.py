"""WORLDTRACE UI v6 navigation and interactive card regression checks."""
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]/"static"
HTML=(BASE/"index.html").read_text(encoding="utf-8")
JS=(BASE/"app.js").read_text(encoding="utf-8")
CSS=(BASE/"style.css").read_text(encoding="utf-8")

def test_real_human_review_route_exists():
    assert 'data-route="reviews"' in HTML
    assert 'id="reviews" class="page"' in HTML
    assert "renderReviewQueue()" in JS
    assert 'id="reviewMissionSelect"' in HTML

def test_all_cards_have_real_click_and_keyboard_handlers():
    assert 'data-launch-tool=' in JS
    assert "addEventListener('click',action)" in JS
    assert "e.key==='Enter'||e.key===' '" in JS
    assert "function launchTool(tool)" in JS

def test_mission_and_audit_navigation():
    assert 'id="topNewMission"' in HTML
    assert 'id="jumpReview"' in HTML
    assert "function showAudit(id)" in JS
    assert "$('auditMission').onchange" in JS

def test_review_controls_wired_to_authenticated_backend():
    assert "submitRecoveryReview(id,b.dataset.reviewTool,b.dataset.reviewDecision)" in JS
    assert "'X-WORLDTRACE-TOKEN':token" in JS

def test_cache_busted_styles_and_scripts():
    import re
    css=re.search(r'/assets/style\.css\?v=(\d+)',HTML)
    js=re.search(r'/assets/app\.js\?v=(\d+)',HTML)
    assert css and js and css.group(1)==js.group(1)
    assert '.interactive-card:hover' in CSS
