"""WORLDTRACE API and Mission Control application."""
from pathlib import Path
import os
import secrets
from fastapi import FastAPI, HTTPException, Header, File, UploadFile, Form
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from worldtrace import agent,engine,storage,tools,samples,delivery,uploads,multifile,unified_records,sandbox_recovery,public_demo

app=FastAPI(title='WORLDTRACE',version='0.1.0',description='Verifiable local workflow prototype with optional actual Meta-model orchestration')
STATIC=Path(__file__).parent/'static'
app.mount('/assets',StaticFiles(directory=STATIC),name='assets')

class MissionIn(BaseModel):
    goal:str=Field(min_length=12,max_length=1500)
    mode:str='local'

class DeliverableIn(BaseModel):
    goal: str=Field(min_length=12,max_length=1500)
    evidence: str=Field(default='',max_length=12000)
    domain: str='supplier_onboarding'

class DemoCorrectionIn(BaseModel):
    action_index: int = Field(ge=0)

class UnifiedDecisionIn(BaseModel):
    action_index: int = Field(ge=0)
    decision: str
    reviewer: str = Field(min_length=2,max_length=80)
    note: str = Field(default='',max_length=500)

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


@app.post('/api/deliverables',status_code=201)
def create_deliverable(req:DeliverableIn, x_worldtrace_token: str | None = Header(default=None)):
    """Protected genuine artifact generation; explicitly deterministic, not Meta AI."""
    require_mission_token(x_worldtrace_token)
    try:return delivery.produce(req.goal, req.evidence, req.domain)
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc

@app.get('/api/deliverables/{deliverable_id}/download')
def download_deliverable(deliverable_id:str, x_worldtrace_token: str | None = Header(default=None)):
    require_mission_token(x_worldtrace_token)
    import re
    if not re.fullmatch(r'WD-[A-F0-9]{12}', deliverable_id):
        raise HTTPException(404,'Deliverable not found')
    path=storage.root()/'deliverables'/deliverable_id/f'{deliverable_id}.zip'
    if not path.is_file():raise HTTPException(404,'Deliverable not found')
    return FileResponse(path,media_type='application/zip',filename=f'{deliverable_id}.zip')


@app.post('/api/tools/{tool_id}/inspect-upload')
async def inspect_uploaded_file(tool_id:str,
    file:UploadFile=File(...),
    comparison:UploadFile | None=File(default=None),
    x_worldtrace_token: str | None=Header(default=None)):
    """Authenticated in-memory inspection of user-provided data (no storage)."""
    require_mission_token(x_worldtrace_token)
    if tool_id not in uploads.FORMATS:
        raise HTTPException(404,'Real-file inspection not available for this tool')
    try:
        raw=await file.read(uploads.MAX_BYTES+1)
        compare_raw=None
        if comparison is not None:
            if tool_id!='etl_compare' or not (comparison.filename or '').lower().endswith('.csv'):
                raise ValueError('Comparison is only available for ETL CSV target files')
            compare_raw=await comparison.read(uploads.MAX_BYTES+1)
        return uploads.inspect(tool_id,file.filename or '',raw,compare_raw)
    except (ValueError,UnicodeError,KeyError,TypeError,IndexError,ImportError) as exc:
        raise HTTPException(422,str(exc)[:220]) from exc
    except Exception as exc:
        # Malformed third-party PDF/JSON parser data must not crash the API or leak internals.
        raise HTTPException(422,'Unable to parse uploaded file; verify its format and content') from exc
    finally:
        await file.close()
        if comparison is not None:await comparison.close()

@app.post('/api/multi-file-missions/run')
async def run_uploaded_multi_file_mission(
    goal: str = Form(...),
    retain_result: bool = Form(default=False),
    model_planning: bool = Form(default=False),
    pdf: UploadFile | None = File(default=None),
    email: UploadFile | None = File(default=None),
    har: UploadFile | None = File(default=None),
    source_csv: UploadFile | None = File(default=None),
    target_csv: UploadFile | None = File(default=None),
    api_json: UploadFile | None = File(default=None),
    messages_json: UploadFile | None = File(default=None),
    legacy_txt: UploadFile | None = File(default=None),
    x_worldtrace_token: str | None = Header(default=None),
):
    """One private instruction, coordinated real-file checks and report. No files stored."""
    require_mission_token(x_worldtrace_token)
    fields = {"pdf": pdf, "email": email, "har": har, "source_csv": source_csv,
              "target_csv": target_csv, "api_json": api_json,
              "messages_json": messages_json, "legacy_txt": legacy_txt}
    selected = {}
    try:
        for role, upload in fields.items():
            if upload is not None:
                selected[role] = (upload.filename or "", await upload.read(uploads.MAX_BYTES + 1))
        try:
            model_plan=None
            if model_planning:
                try:model_plan=agent.make_uploaded_file_plan(goal,list(selected))
                except agent.ModelUnavailable as exc:raise HTTPException(424,str(exc)) from exc
            result=multifile.run(goal, selected, model_plan=model_plan,
                reasoner=agent.assess_uploaded_evidence if model_planning else None)
            if retain_result:
                record=unified_records.record(result)
                result['saved_mission_id']=record['id']
                result['retention']='Derived findings and report saved in SQLite (no raw files); may be lost on free Render restart'
            return result
        except HTTPException:
            raise
        except agent.ModelUnavailable as exc:
            raise HTTPException(424,str(exc)) from exc
        except (ValueError, UnicodeError, KeyError, TypeError) as exc:
            raise HTTPException(422, str(exc)[:220]) from exc
        except Exception as exc:
            raise HTTPException(422, "Unable to process one of the uploaded files") from exc
    finally:
        for upload in fields.values():
            if upload is not None:
                await upload.close()

@app.get('/api/unified-missions')
def unified_listing(x_worldtrace_token: str | None = Header(default=None)):
    require_mission_token(x_worldtrace_token)
    return unified_records.listing()

@app.get('/api/unified-missions/{mission_id}')
def unified_detail(mission_id:str,x_worldtrace_token: str | None = Header(default=None)):
    require_mission_token(x_worldtrace_token)
    try:return unified_records.get(mission_id)
    except ValueError as exc:raise HTTPException(404,str(exc)) from exc

@app.post('/api/unified-missions/{mission_id}/decisions',status_code=201)
def unified_decision(mission_id:str,req:UnifiedDecisionIn,
                     x_worldtrace_token: str | None = Header(default=None)):
    require_mission_token(x_worldtrace_token)
    try:return unified_records.decide(mission_id,req.action_index,req.decision,req.reviewer,req.note)
    except ValueError as exc:
        raise HTTPException(404 if 'not found' in str(exc) else 409,str(exc)) from exc

@app.post('/api/model/probe')
def probe_model_inference(x_worldtrace_token: str | None = Header(default=None)):
    """Explicit short, potentially billable test request. No private source data sent."""
    require_mission_token(x_worldtrace_token)
    try:return agent.probe_provider()
    except agent.ModelUnavailable as exc:raise HTTPException(424,str(exc)) from exc

@app.post('/api/unified-missions/{mission_id}/execute-demo-correction',status_code=201)
def execute_approved_demo_correction(mission_id:str, req:DemoCorrectionIn,
                     x_worldtrace_token: str | None=Header(default=None)):
    """Approved sandbox-only row correction, with transaction and exact re-verification."""
    require_mission_token(x_worldtrace_token)
    try:return sandbox_recovery.execute(mission_id,req.action_index)
    except ValueError as exc:
        raise HTTPException(404 if 'Mission not found' in str(exc) else 409,str(exc)) from exc

@app.post('/api/public-demo/start',status_code=201)
def start_public_guided_demo():
    """Synthetic-only, bounded, short-lived and zero-secret demonstration."""
    try:return public_demo.start()
    except RuntimeError as exc:raise HTTPException(429,str(exc)) from exc

@app.get('/api/public-demo/{demo_id}')
def get_public_guided_demo(demo_id:str):
    try:return public_demo.get(demo_id)
    except ValueError as exc:raise HTTPException(404,str(exc)) from exc

@app.post('/api/public-demo/{demo_id}/approve')
def approve_public_guided_demo(demo_id:str):
    try:return public_demo.approve(demo_id)
    except ValueError as exc:
        raise HTTPException(404 if "expired" in str(exc) or "not found" in str(exc) else 409,str(exc)) from exc

@app.post('/api/public-demo/{demo_id}/execute')
def execute_public_guided_demo(demo_id:str):
    try:return public_demo.execute(demo_id)
    except ValueError as exc:
        raise HTTPException(404 if "expired" in str(exc) or "not found" in str(exc) else 409,str(exc)) from exc
