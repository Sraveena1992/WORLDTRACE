"""WORLDTRACE API and Mission Control application."""
from pathlib import Path
import os
import secrets
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from worldtrace import agent,engine,storage,tools,samples

app=FastAPI(title='WORLDTRACE',version='0.1.0',description='Verifiable local workflow prototype with optional actual Meta-model orchestration')
STATIC=Path(__file__).parent/'static'
app.mount('/assets',StaticFiles(directory=STATIC),name='assets')

class MissionIn(BaseModel):
    goal:str=Field(min_length=12,max_length=1500)
    mode:str='local'

class RecoveryReviewIn(BaseModel):
    tool: str=Field(min_length=2,max_length=64)
    decision: str
    reviewer: str=Field(min_length=2,max_length=80)
    note: str=Field(default='',max_length=500)

def require_mission_token(token):
    expected=os.getenv('WORLDTRACE_MISSION_TOKEN','')
    if not expected:
        raise HTTPException(503,'Private mission review and model operations are disabled')
    if not token or not secrets.compare_digest(token,expected):
        raise HTTPException(403,'Private mission authorization required')

@app.on_event('startup')
def startup():samples.ensure()

@app.get('/')
def home():return FileResponse(STATIC/'index.html')

@app.get('/healthz')
def health():return {'status':'ok','service':'worldtrace','version':'0.1.0'}

@app.get('/api/capabilities')
def capabilities():
    return {'meta_model_configured':agent.configured(),'model_name':__import__('os').getenv('WORLDTRACE_MODEL_NAME','meta-models/muse-spark-open-1026'),
            'local_workflow_available':True,'model_mode_available':agent.configured(),'tools':tools.TOOL_INFO,'connected_external_services':0,
            'message':'LOCAL workflow mode is deterministic, NOT autonomous model inference; only MODEL mode uses actual configured inference.'}

@app.get('/api/missions')
def missions():return storage.listing()

@app.post('/api/missions',status_code=202)
def create(req:MissionIn, x_worldtrace_token: str | None = Header(default=None)):
    if req.mode not in ('local','model'):raise HTTPException(422,'mode must be local or model')
    if req.mode == 'model':
        require_mission_token(x_worldtrace_token)
    try:mid=engine.start(req.goal,req.mode)
    except agent.ModelUnavailable as ex:raise HTTPException(424,str(ex))
    return {'id':mid,'status':'queued','mode':req.mode}

@app.get('/api/missions/{mission_id}')
def mission(mission_id:str):
    result=storage.get(mission_id)
    if result is None:raise HTTPException(404,'Mission not found')
    result['audit_chain_valid']=storage.verify_chain(mission_id)
    return result

@app.get('/api/missions/{mission_id}/report')
def report(mission_id:str):
    if not storage.get(mission_id):raise HTTPException(404,'Mission not found')
    p=storage.root()/'reports'/f'{mission_id}.md'
    if not p.exists():raise HTTPException(409,'Report is not ready')
    return PlainTextResponse(p.read_text(),headers={'Content-Disposition':f'attachment; filename="{mission_id}.md"'})

@app.post('/api/missions/{mission_id}/reviews',status_code=201)
def review_recovery(mission_id:str, req:RecoveryReviewIn, x_worldtrace_token: str | None = Header(default=None)):
    require_mission_token(x_worldtrace_token)
    if req.decision not in ('approve_for_manual_followup','reject'):
        raise HTTPException(422,'decision must be approve_for_manual_followup or reject')
    try:
        return storage.record_review(mission_id,req.tool,req.decision,req.reviewer,req.note)
    except ValueError as exc:
        raise HTTPException(404 if str(exc)=='Mission not found' else 409,str(exc)) from exc

@app.get('/api/missions/{mission_id}/reviews')
def list_recovery_reviews(mission_id:str, x_worldtrace_token: str | None = Header(default=None)):
    require_mission_token(x_worldtrace_token)
    if not storage.get(mission_id):raise HTTPException(404,'Mission not found')
    return storage.reviews(mission_id)


@app.get('/api/tools/{tool_id}/workspace')
def tool_workspace(tool_id:str):
    """Describe the exact fixture input and procedure for one bounded tool."""
    if tool_id not in tools.AVAILABLE:raise HTTPException(404,'Tool not available')
    from worldtrace.tool_workspaces import DETAILS
    return {'tool':tool_id,**DETAILS[tool_id], 'access':'Synthetic test fixtures only; no external account integration'}

@app.post('/api/tools/{tool_id}/runs',status_code=201)
def run_single_tool(tool_id:str):
    """Run an allowlisted fixture tool as a standalone inspection, not an AI mission."""
    if tool_id not in tools.AVAILABLE:raise HTTPException(404,'Tool not available')
    samples.ensure()
    try:
        result=tools.execute(tool_id)
        status='passed' if result.get('pass') else 'finding'
    except Exception as exc:
        result={'error':str(exc)[:240]}
        status='error'
    return storage.record_tool_run(tool_id,status,result)

@app.get('/api/tools/{tool_id}/runs')
def tool_run_history(tool_id:str):
    if tool_id not in tools.AVAILABLE:raise HTTPException(404,'Tool not available')
    return storage.list_tool_runs(tool_id)

@app.get('/api/tool-runs/{run_id}')
def tool_run_detail(run_id:str):
    run=storage.get_tool_run(run_id)
    if run is None:raise HTTPException(404,'Run not found')
    return run
