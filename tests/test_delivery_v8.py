"""Outcome Studio produces genuine, integrity-checked downloadable artifacts."""
import io
import json
import zipfile
from fastapi.testclient import TestClient
import app
from worldtrace import delivery

client=TestClient(app.app)
TOKEN="unit-test-mission-token"

def test_protected_delivery_workflow(monkeypatch):
    monkeypatch.setenv("WORLDTRACE_MISSION_TOKEN",TOKEN)
    request={
      "goal":"Investigate and resolve a synthetic supplier onboarding exception with evidence",
      "evidence":"Document is unsigned\nETL record A03 missing\nAPI returned 503",
      "domain":"supplier_onboarding",
    }
    assert client.post("/api/deliverables",json=request).status_code==403
    headers={"X-WORLDTRACE-TOKEN":TOKEN}
    result=client.post("/api/deliverables",json=request,headers=headers)
    assert result.status_code==201,result.text
    data=result.json()
    assert data["status"]=="DELIVERED_LOCAL_PACKAGE"
    assert data["mode"]=="deterministic_local"
    assert len(data["events"])==6
    assert all(data["verification"].values())
    assert client.get(data["download_url"]).status_code==403
    zip_result=client.get(data["download_url"],headers=headers)
    assert zip_result.status_code==200
    with zipfile.ZipFile(io.BytesIO(zip_result.content)) as z:
        assert z.testzip() is None
        assert {"research_brief.md","action_plan.json","evidence.json","manifest.json","trace.json"} == set(z.namelist())
        trace=json.loads(z.read("trace.json"))
        assert [e["agent"] for e in trace]==["Research Agent","Builder Agent","Security Agent","Execution Agent","Verification Agent","Delivery Agent"]
        plan=json.loads(z.read("action_plan.json"))
        assert len(plan["actions"])==3
        assert all(item["status"]=="PROPOSED_NOT_EXECUTED" for item in plan["actions"])

def test_delivery_rejects_unsupported_domain_and_invalid_id(monkeypatch):
    monkeypatch.setenv("WORLDTRACE_MISSION_TOKEN",TOKEN)
    h={"X-WORLDTRACE-TOKEN":TOKEN}
    assert client.post("/api/deliverables",json={"goal":"Investigate this synthetic issue","domain":"arbitrary_shell"},headers=h).status_code==422
    assert client.get("/api/deliverables/bad/download",headers=h).status_code==404

def test_input_bounds():
    try:delivery.validate("good goal for testing","x"*12001,"supplier_onboarding")
    except ValueError:pass
    else:raise AssertionError("Evidence size limit not enforced")
