"""WORLDTRACE API and Mission Control application."""
from pathlib import Path
from fastapi import FastAPI, HTTPException
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
def create(req:MissionIn):
    if req.mode not in ('local','model'):raise HTTPException(422,'mode must be local or model')
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
