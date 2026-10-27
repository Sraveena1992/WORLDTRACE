from worldtrace import recovery

def test_proposals_only_for_nonpassing_tasks():
    tasks = [
        {"tool": "pdf_inspect", "status": "finding", "result": {"pass": False}},
        {"tool": "etl_compare", "status": "blocked", "result": {}},
        {"tool": "email_inspect", "status": "passed", "result": {"pass": True}},
    ]
    actions = recovery.recommend(tasks)
    assert [item["tool"] for item in actions] == ["pdf_inspect", "etl_compare"]
    assert all(item["execution"].startswith("NOT EXECUTED") for item in actions)
    assert all(item["owner"] and item["proposed_action"] for item in actions)

def test_no_proposals_for_clean_execution():
    assert recovery.recommend([{"tool": "email_inspect", "status": "passed"}]) == []

def test_unknown_tool_has_safe_fallback():
    item = recovery.recommend([{"tool": "unknown", "status": "error"}])[0]
    assert item["owner"] == "Mission owner"
    assert "manually" in item["proposed_action"]
