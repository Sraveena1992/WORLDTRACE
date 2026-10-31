"""Navigation clarity: separate WT- fixture history from UM- and public demo missions."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"static/index.html").read_text(encoding="utf-8")
JS=(ROOT/"static/app.js").read_text(encoding="utf-8")

def test_agent_workforce_has_no_secret_public_demo_entry():
    assert 'id="agentStartDemo"' in HTML
    assert 'id="agentLoadStatus"' in HTML
    assert 'id="loadSavedAgentMissions"' in HTML
    assert "route('multi');" in JS
    assert "$('startPublicDemo').scrollIntoView" in JS
    assert "Private UM- history requires" in JS

def test_fixture_refresh_is_explicit_and_visible():
    assert 'id="fixtureRefreshStatus"' in HTML
    assert "WT- mission(s) currently recorded" in JS
    assert "This does not load public demo or UM- mission records" in JS

def test_agent_cards_offer_real_evidence_inspection():
    assert 'data-role-detail=' in JS
    assert "function renderAgentWorkforce()" in JS
    assert "app.unifiedMissions.unshift(item)" in JS
    assert 'id="agentRoleDetail"' in HTML
    assert 'app.js?v=24' in HTML
