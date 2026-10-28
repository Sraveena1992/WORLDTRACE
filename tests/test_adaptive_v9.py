"""Adaptive two-round model orchestration regression tests."""
import time
import pytest
from worldtrace import adaptive, agent, engine, storage

def test_model_followup_rejects_unsafe_or_repeated_tools():
    executed=["pdf_inspect","email_inspect"]
    with pytest.raises(adaptive.InvalidPlan):
        adaptive.validate_followup({"steps":[{"id":"x","tool":"pdf_inspect","depends_on":[]}]},executed)
    with pytest.raises(adaptive.InvalidPlan):
        adaptive.validate_followup({"steps":[{"id":"x","tool":"shell_exec","depends_on":[]}]},executed)

def test_model_followup_stops_or_selects_relevant_remaining_checks():
    executed=["pdf_inspect","email_inspect"]
    stop=adaptive.validate_followup({"finish":True,"reason":"Evidence sufficient"},executed)
    assert stop["finish"] and stop["tasks"]==[]
    plan=adaptive.validate_followup({"finish":False,"steps":[
        {"id":"net","tool":"network_inspect","depends_on":[]},
        {"id":"api","tool":"api_virtualize","depends_on":["net"]}]},executed)
    assert plan["tasks"]==["network_inspect","api_virtualize"]

def test_bounded_second_round_executes_and_logs_events(monkeypatch,tmp_path):
    monkeypatch.setenv("WORLDTRACE_DATA_DIR",str(tmp_path))
    from worldtrace import samples
    samples.ensure()
    monkeypatch.setattr(agent,"configured",lambda:True)
    monkeypatch.setattr(agent,"make_plan",lambda goal,use_model:{
        "mode":"meta-model","reason":"Mocked test plan","steps":[
            {"id":"first","tool":"pdf_inspect","depends_on":[],"objective":"Read PDF"},
            {"id":"second","tool":"email_inspect","depends_on":[],"objective":"Read email"}]})
    monkeypatch.setattr(agent,"make_followup_plan",lambda goal,tasks:{
        "mode":"meta-model-followup","finish":False,"reason":"Check network and contract",
        "provider_response_id":"mock-only","steps":[
            {"id":"net","tool":"network_inspect","depends_on":[],"objective":"Inspect HAR"},
            {"id":"api","tool":"api_virtualize","depends_on":["net"],"objective":"Inspect API"}]})
    mid=storage.make_mission("Investigate synthetic supplier onboarding failure","model")
    engine.run(mid,"Investigate synthetic supplier onboarding failure","model")
    m=storage.get(mid)
    assert m["status"]=="completed",m["error"]
    assert len(m["tasks"])==4
    assert {t["tool"] for t in m["tasks"]}=={"pdf_inspect","email_inspect","network_inspect","api_virtualize"}
    assert any(e["kind"]=="agent.followup_decision" for e in m["events"])
    assert len([e for e in m["events"] if e["kind"]=="tool.completed" and e["payload"].get("round")==2])==2
    assert storage.verify_chain(mid)
    assert "Second-round Meta decision" in (storage.root()/"reports"/(mid+".md")).read_text()

def test_local_mode_does_not_invoke_model_followup(monkeypatch,tmp_path):
    monkeypatch.setenv("WORLDTRACE_DATA_DIR",str(tmp_path))
    from worldtrace import samples
    samples.ensure()
    def forbidden(*args):
        raise AssertionError("Local mode must not call model follow-up")
    monkeypatch.setattr(agent,"make_followup_plan",forbidden)
    mid=storage.make_mission("Inspect PDF signatures and email notices","local")
    engine.run(mid,"Inspect PDF signatures and email notices","local")
    m=storage.get(mid)
    assert m["status"]=="completed"
    assert not any(e["kind"]=="agent.followup_decision" for e in m["events"])
