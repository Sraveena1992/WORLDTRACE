"""Judge-facing integration tests: real provider protocol, exact role coverage and token budget.

These tests mock the transport; they are NOT proof that Baseten access works.
"""
import json
import pytest
from worldtrace import agent

class FakeResponse:
    def __init__(self, content):
        self.payload={"id":"fake-transport-response","model":"meta-models/muse-spark-open",
            "choices":[{"message":{"content":content}}]}
    def raise_for_status(self): pass
    def json(self):return self.payload

class FakeClient:
    payloads=[]
    response_text="READY"
    def __init__(self,timeout):self.timeout=timeout
    def __enter__(self):return self
    def __exit__(self,*args):return None
    def post(self,url,json,headers):
        FakeClient.payloads.append((url,json,headers))
        return FakeResponse(FakeClient.response_text)

def configure(monkeypatch):
    monkeypatch.setenv("WORLDTRACE_MODEL_BASE_URL","https://example.invalid/v1")
    monkeypatch.setenv("WORLDTRACE_MODEL_API_KEY","test-key-only")
    monkeypatch.setenv("WORLDTRACE_MODEL_NAME","meta-models/muse-spark-open")
    FakeClient.payloads=[]
    monkeypatch.setattr(agent.httpx,"Client",FakeClient)

def test_probe_has_room_for_reasoning_and_no_uploaded_evidence(monkeypatch):
    configure(monkeypatch)
    FakeClient.response_text="READY"
    result=agent.probe_provider()
    assert result["inference_verified"]
    url,payload,headers=FakeClient.payloads[0]
    assert url.endswith("/v1/chat/completions")
    assert payload["max_tokens"]>=1024
    assert "Connectivity check" in str(payload)
    assert headers["Authorization"]=="Bearer test-key-only"

def test_file_plan_accepts_exact_roles_with_provider_id(monkeypatch):
    configure(monkeypatch)
    FakeClient.response_text=json.dumps({"ordered_roles":["target_csv","source_csv"],
        "reason":"Inspect target and source"})
    result=agent.make_uploaded_file_plan("Investigate missing supplier",["source_csv","target_csv"])
    assert result["ordered_roles"]==["target_csv","source_csv"]
    assert result["provider_response_id"]=="fake-transport-response"
    assert FakeClient.payloads[0][1]["max_tokens"]>=4096

def test_file_plan_rejects_unapproved_role(monkeypatch):
    configure(monkeypatch)
    FakeClient.response_text=json.dumps({"ordered_roles":["source_csv","shell_exec"],
        "reason":"Run shell"})
    with pytest.raises(agent.ModelUnavailable,match="file planning unavailable"):
        agent.make_uploaded_file_plan("Investigate missing supplier",["source_csv","target_csv"])
