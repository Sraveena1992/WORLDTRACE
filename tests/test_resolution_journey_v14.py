"""Acceptance checks for final integrated guided demo and model evidence policy."""
import json
from pathlib import Path
from worldtrace import agent, multifile

def test_recorded_evidence_chain_is_recomputed():
    source={"source_csv":("source.csv",b"id,name\nA1,Alpha\nA2,Beta\n"),
            "target_csv":("target.csv",b"id,name\nA1,Alpha\n")}
    result=multifile.run("Investigate and verify uploaded supplier data",source)
    assert multifile.verify_trace(result["trace"]) is True
    mutated=json.loads(json.dumps(result["trace"]))
    mutated[0]["details"]["source"]="fabricated"
    assert multifile.verify_trace(mutated) is False

def test_model_reasoner_sends_aggregates_not_raw_rows(monkeypatch):
    monkeypatch.setenv("WORLDTRACE_MODEL_BASE_URL","https://example.invalid/v1")
    monkeypatch.setenv("WORLDTRACE_MODEL_API_KEY","test-local-only")
    monkeypatch.setenv("WORLDTRACE_MODEL_NAME","meta-models/muse-spark-open")
    class FakeResponse:
        def raise_for_status(self):pass
        def json(self):
            return {"id":"TEST-COMPLETION","model":"meta-models/muse-spark-open",
                    "choices":[{"message":{"content":json.dumps({
                      "summary":"One record is missing from target",
                      "hypotheses":[{"claim":"Incomplete import","evidence_roles":["source_csv"],
                                     "confidence":"medium"}],
                      "next_action":"Request approval for isolated reconciliation"})}}]}
    class FakeClient:
        def __init__(self,timeout):self.timeout=timeout
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def post(self,url,json,headers):
            serialized=str(json)
            assert "SECRET-CUSTOMER-NAME" not in serialized
            assert "CONFIDENTIAL-ROW-ID" not in serialized
            assert "source_csv" in serialized
            assert url=="https://example.invalid/v1/chat/completions"
            return FakeResponse()
    monkeypatch.setattr(agent.httpx,"Client",FakeClient)
    observations=[{"role":"source_csv","tool":"etl_compare","status":"finding",
       "result":{"source_rows":3,"target_rows":2,"missing_ids":["CONFIDENTIAL-ROW-ID"],
                 "excerpt":"SECRET-CUSTOMER-NAME"}}]
    assessment=agent.assess_uploaded_evidence("Investigate supplier data migration",observations,[])
    assert assessment["hypotheses"][0]["evidence_roles"]==["source_csv"]
    assert assessment["provided_evidence"]=="Sanitized role IDs, statuses, and counts only"

def test_guided_demo_and_integrated_workspaces_have_real_controls():
    root=Path(__file__).resolve().parents[1]
    html=(root/"static/index.html").read_text(encoding="utf-8")
    js=(root/"static/app.js").read_text(encoding="utf-8")
    for marker in ('id="loadGuidedDemo"','id="guidedDemoStatus"','id="agentRoleDetail"',
                   'id="loadSavedAgentMissions"','id="auditUnifiedMission"',
                   'id="loadUnifiedAudit"','id="loadMissionIntoOutcome"'):
        assert marker in html
    for marker in ("new File(", "execute-demo-correction", "function summarizeObservation",
                   "function showUnifiedAudit(", "function importLatestUnifiedEvidence(",
                   "data-role-detail", "data.model_assessment"):
        assert marker in js
    assert (root/"scripts/demo_resolution.py").is_file()
    assert '/assets/app.js?v=24' in html
