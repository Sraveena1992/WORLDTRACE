import json, threading, traceback
from pathlib import Path
from . import agent,storage,tools

AGENT_NAMES={'pdf_inspect':'Document Analyst','email_inspect':'Communications Analyst','network_inspect':'Network Investigator','etl_compare':'Data Integrity Agent','database_check':'Database Auditor','api_virtualize':'API Simulator','performance_probe':'Performance Engineer','middleware_test':'Integration Tester','mainframe_contract':'Legacy Systems Analyst'}

def start(goal,mode='local'):
    if mode not in ('local','model'):raise ValueError('Unknown mode')
    if mode=='model' and not agent.configured():raise agent.ModelUnavailable('Meta inference not configured: use local workflow or configure a real API endpoint.')
    mid=storage.make_mission(goal,mode)
    storage.event(mid,'mission.created',{'goal':goal,'mode':mode,'note':'local workflow is deterministic; model mode requires real inference'})
    t=threading.Thread(target=run,args=(mid,goal,mode),daemon=True);t.start()
    return mid

def run(mid,goal,mode):
    try:
        storage.update_mission(mid,'planning')
        plan=agent.make_plan(goal,mode=='model')
        storage.event(mid,'plan.generated',plan)
        tasks=[]
        for pos,tool in enumerate(plan['tasks']):
            tasks.append((storage.add_task(mid,AGENT_NAMES[tool],tool,pos),tool))
        storage.update_mission(mid,'running')
        for tid,tool in tasks:
            storage.update_task(tid,'running');storage.event(mid,'tool.started',{'tool':tool,'task_id':tid,'agent':AGENT_NAMES[tool]})
            try:
                result=tools.execute(tool)
                status='passed' if result.get('pass') else 'finding'
                storage.update_task(tid,status,result)
                storage.event(mid,'tool.completed',{'tool':tool,'task_id':tid,'status':status,'result':result})
            except Exception as ex:
                storage.update_task(tid,'error',{'error':str(ex)[:250]})
                storage.event(mid,'tool.failed',{'tool':tool,'task_id':tid,'error':str(ex)[:250]})
        details=storage.get(mid);counts={key:sum(t['status']==key for t in details['tasks']) for key in ('passed','finding','error')}
        verdict='needs-review' if counts['finding'] or counts['error'] else 'verified'
        storage.event(mid,'verification.completed',{'verdict':verdict,'counts':counts,'method':'deterministic tool assertions; not independent physical-world proof'})
        # Produce a real Markdown artifact with measured outputs; do not mark findings as successful.
        report=['# WORLDTRACE | Mission Evidence Report','',f'**Mission:** {mid}',f'**Goal:** {goal}',f'**Execution mode:** {details["mode"]}',f'**Verification:** {verdict}','',
                '## Tool results']
        for t in details['tasks']:
            report += [f'### {t["name"]} — {t["status"]}','```json',json.dumps(t['result'],indent=2,default=str),'```','']
        report += ['## Reliability notes','- Evidence comes from included synthetic LOCAL sample fixtures.','- A tool passing its assertion is not proof that an external enterprise environment was tested.',
                   '- Model mode requires a real working configured Meta-compatible inference endpoint.',
                   '- External writes, email sends, and production fixes are NOT performed by this build.']
        target=storage.root()/'reports';target.mkdir(exist_ok=True)
        (target/f'{mid}.md').write_text('\n'.join(report),encoding='utf-8')
        storage.event(mid,'report.generated',{'artifact':f'{mid}.md','verdict':verdict})
        storage.update_mission(mid,'completed')
    except Exception as ex:
        storage.event(mid,'mission.error',{'error':str(ex)[:450]})
        storage.update_mission(mid,'error',str(ex)[:450])
