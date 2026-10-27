from worldtrace import agent
from worldtrace.local_routing import select_local_tools

def test_select_narrow_pdf_email_mission():
    tools, rationale = select_local_tools("Inspect PDF signatures and email notices")
    assert tools == ["pdf_inspect", "email_inspect"]
    assert "NOT AI" in rationale

def test_broad_supplier_mission_keeps_all_tools():
    plan = agent.make_plan("Investigate synthetic supplier onboarding failures", False)
    assert len(plan["steps"]) == 9
    assert plan["mode"] == "local-workflow"

def test_ambiguous_goal_keeps_safe_full_coverage():
    tools, rationale = select_local_tools("Inspect approved records")
    assert len(tools) == 9

def test_specific_local_plan_is_allowlisted():
    plan = agent.make_plan("Inspect PDF signatures and email notices", False)
    assert plan["tasks"] == ["pdf_inspect", "email_inspect"]
    assert len(plan["steps"]) == 2
