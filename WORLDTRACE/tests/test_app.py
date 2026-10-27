import os, time
from fastapi.testclient import TestClient
os.environ['WORLDTRACE_DATA_DIR']='runtime-test'
from app import app
from worldtrace import storage,samples,tools

samples.ensure()
client=TestClient(app)

def test_health():assert client.get('/healthz').json()['status']=='ok'
def test_capabilities():
    j=client.get('/api/capabilities').json()
    assert len(j['tools'])==9 and j['local_workflow_available']

def test_reject_short_mission():assert client.post('/api/missions',json={'goal':'abc','mode':'local'}).status_code==422

def test_model_requires_key(monkeypatch):
    monkeypatch.delenv('WORLDTRACE_MODEL_BASE_URL',raising=False);monkeypatch.delenv('WORLDTRACE_MODEL_API_KEY',raising=False)
    assert client.post('/api/missions',json={'goal':'Inspect the supplier onboarding files','mode':'model'}).status_code==424

def test_real_tools():
    results={name:tools.execute(name) for name in tools.AVAILABLE}
    assert set(results)==tools.AVAILABLE
    assert results['pdf_inspect']['pass'] is False
    assert results['network_inspect']['failure_count']==1
    assert results['etl_compare']['missing_ids']==['A03']
    assert results['database_check']['pending']==1
    assert results['email_inspect']['pass'] is True
    assert results['api_virtualize']['pass'] is False
    assert results['middleware_test']['pass'] is False
    assert results['performance_probe']['samples']==20

def test_full_mission_creates_real_artifact_and_audit():
    res=client.post('/api/missions',json={'goal':'Investigate why supplier onboarding has failed and produce evidence','mode':'local'})
    assert res.status_code==202,res.text
    mid=res.json()['id']
    for i in range(120):
        d=client.get('/api/missions/'+mid).json()
        if d['status'] in ('completed','error'):break
        time.sleep(.05)
    assert d['status']=='completed',d
    assert len(d['tasks'])==9
    assert d['audit_chain_valid']
    assert len(d['events'])>=22
    assert any(t['status']=='finding' for t in d['tasks'])
    body=client.get(f'/api/missions/{mid}/report')
    assert body.status_code==200 and 'needs-review' in body.text and mid in body.text

def test_path_traversal_blocked():
    from worldtrace.tools import safe_path
    import pytest
    with pytest.raises(ValueError):safe_path('../../etc/passwd')
