import json
import pytest
from worldtrace import agent, planning, verification

def test_dependency_order():
    plan = planning.validate_plan({"steps": [
        {"id":"second","tool":"etl_compare","depends_on":["first"]},
        {"id":"first","tool":"pdf_inspect","depends_on":[]}]})
    assert plan["tasks"] == ["pdf_inspect","etl_compare"]

@pytest.mark.parametrize("invalid", [
    {"tasks":["pdf_inspect","pdf_inspect"]},
    {"tasks":["pdf_inspect","delete_all_records"]},
    {"steps":[{"id":"a","tool":"pdf_inspect","depends_on":["b"]},{"id":"b","tool":"etl_compare","depends_on":["a"]}]},
    {"steps":[{"id":"a","tool":"pdf_inspect","depends_on":["missing"]},{"id":"b","tool":"etl_compare","depends_on":[]}]},
    {"tasks":["pdf_inspect"]},
])
def test_reject_unsafe_plan(invalid):
    with pytest.raises(planning.InvalidPlan):
        planning.validate_plan(invalid)

def test_local_mode_is_not_ai():
    plan = agent.make_plan("Inspect approved records", False)
    assert plan["mode"] == "local-workflow"
    assert len(plan["steps"]) == 9

def test_mock_provider_plan_validation(monkeypatch):
    monkeypatch.setenv("WORLDTRACE_MODEL_BASE_URL","https://provider.example/v1")
    monkeypatch.setenv("WORLDTRACE_MODEL_API_KEY","fake-test-only")
    class Response:
        def raise_for_status(self): pass
        def json(self): return {"id":"mock-response", "model":"meta-test-model","choices":[{"message":{"content":json.dumps({"steps":[{"id":"a","tool":"pdf_inspect","depends_on":[]},{"id":"b","tool":"etl_compare","depends_on":["a"]}]})}}]}
    class Client:
        def __init__(self,timeout): pass
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def post(self,url,json,headers):
            assert url == "https://provider.example/v1/chat/completions"
            assert headers["Authorization"] == "Bearer fake-test-only"
            return Response()
    monkeypatch.setattr(agent.httpx,"Client",Client)
    plan = agent.make_plan("Check synthetic supplier fixture",True)
    assert plan["tasks"] == ["pdf_inspect","etl_compare"]
    assert plan["provider_response_id"] == "mock-response"

def test_cross_tool_findings():
    finding = verification.verify([
        {"tool":"network_inspect","status":"finding","result":{"failures":[{"status":503}]}},
        {"tool":"api_virtualize","status":"finding","result":{"simulated":503}}])
    assert finding["verdict"] == "needs-review"
    assert finding["cross_checks"][0]["pass"]
