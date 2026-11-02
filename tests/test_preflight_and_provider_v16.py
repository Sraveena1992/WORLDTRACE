"""Final judge gate: invalid user inputs must never burn Muse tokens."""
from fastapi.testclient import TestClient
import app

client=TestClient(app.app)
TOKEN="operator-test-only"

def test_bad_model_mission_never_calls_provider(monkeypatch,tmp_path):
    monkeypatch.setenv("WORLDTRACE_DATA_DIR",str(tmp_path))
    monkeypatch.setenv("WORLDTRACE_MISSION_TOKEN",TOKEN)
    called=[]
    def forbidden(*args,**kwargs):
        called.append(args)
        raise AssertionError("Meta inference must not run on invalid input")
    monkeypatch.setattr(app.agent,"make_uploaded_file_plan",forbidden)
    head={"X-WORLDTRACE-TOKEN":TOKEN}
    scenarios=[
        ({"goal":"Investigate missing vendor supplier records","model_planning":"true"},
         {"source_csv":("source.csv",b"id,name\nA1,Alpha\n","text/csv")}),
        ({"goal":"Investigate missing vendor supplier records","model_planning":"true"},
         {"pdf":("wrong.txt",b"not pdf","text/plain")}),
        ({"goal":"short","model_planning":"true"},
         {"pdf":("sample.pdf",b"%PDF-1.4","application/pdf")}),
        ({"goal":"Investigate missing vendor supplier records","model_planning":"true"},
         {"pdf":("sample.pdf",b"x"*(2*1024*1024+1),"application/pdf")}),
    ]
    for fields, files in scenarios:
        result=client.post("/api/multi-file-missions/run",data=fields,files=files,headers=head)
        assert result.status_code==422,(result.status_code,result.text)
    assert called==[]

def test_probe_distinguishes_permission_denied_without_leaking_body(monkeypatch):
    from worldtrace import agent
    import httpx
    monkeypatch.setenv("WORLDTRACE_MODEL_BASE_URL","https://example.invalid/v1")
    monkeypatch.setenv("WORLDTRACE_MODEL_API_KEY","secret-test-key")
    class FakeClient:
        def __init__(self,timeout):pass
        def __enter__(self):return self
        def __exit__(self,*args):return None
        def post(self,url,json,headers):
            request=httpx.Request("POST",url)
            response=httpx.Response(403,request=request,text="secret-test-key confidential")
            raise httpx.HTTPStatusError("Forbidden",request=request,response=response)
    monkeypatch.setattr(agent.httpx,"Client",FakeClient)
    try:agent.probe_provider()
    except agent.ModelUnavailable as exc:
        message=str(exc)
        assert "403" in message
        assert "organization" in message
        assert "secret-test-key" not in message
        assert "confidential" not in message
    else:raise AssertionError("403 incorrectly treated as successful inference")
