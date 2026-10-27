"""Model-generated tool planning when configured, explicit local fallback otherwise."""
import json, os, urllib.parse, httpx
from .tools import AVAILABLE

DEFAULT_TOOLS=['pdf_inspect','email_inspect','network_inspect','etl_compare','database_check','api_virtualize','performance_probe','middleware_test','mainframe_contract']

class ModelUnavailable(RuntimeError):pass

def configured():return bool(os.getenv('WORLDTRACE_MODEL_BASE_URL') and os.getenv('WORLDTRACE_MODEL_API_KEY'))

def make_plan(goal, use_model):
    if not use_model:
        return {'mode':'local-workflow','reason':'Fixed auditable local workflow; NOT an AI model-driven plan','tasks':DEFAULT_TOOLS}
    if not configured():raise ModelUnavailable('Meta model inference not configured. Set WORLDTRACE_MODEL_BASE_URL and WORLDTRACE_MODEL_API_KEY, or select LOCAL WORKFLOW (non-agentic).')
    base=os.environ['WORLDTRACE_MODEL_BASE_URL'].rstrip('/')
    if not base.startswith('https://'):raise ModelUnavailable('HTTPS inference endpoint required')
    key=os.environ['WORLDTRACE_MODEL_API_KEY'];name=os.getenv('WORLDTRACE_MODEL_NAME','meta-models/muse-spark-open-1026')
    sys=('You are the WORLDTRACE mission planner. Return ONLY JSON {"tasks":[tool_ids],"reason":"brief reason"}. '
         'Choose tool ids from the supplied list. Include at least 2 relevant distinct tools. '
         'Each tool may execute once. Do not claim success. Inputs are local controlled sample fixtures. '
         'Avoid unsupported actions and external side effects. All tool executions will be verified by the server.')
    payload={'model':name,'messages':[{'role':'system','content':sys},{'role':'user','content':json.dumps({'goal':goal,'available_tools':sorted(AVAILABLE)})}], 'temperature':0.2,'max_tokens':700}
    try:
        with httpx.Client(timeout=35) as cli:
            r=cli.post(base+'/chat/completions',json=payload,headers={'Authorization':f'Bearer {key}'})
            r.raise_for_status();response=r.json()
        raw=response['choices'][0]['message']['content']
        if isinstance(raw,list):raw=''.join(x.get('text','') for x in raw if isinstance(x,dict))
        raw=str(raw).strip()
        if raw.startswith('```'):raw=raw.strip('`').replace('json\n','',1).strip()
        obj=json.loads(raw)
        tasks=obj['tasks']
        if not isinstance(tasks,list) or not 2<=len(tasks)<=len(AVAILABLE) or len(set(tasks))!=len(tasks) or not all(t in AVAILABLE for t in tasks):
            raise ValueError('Invalid or unsupported tool plan from model')
        return {'mode':'meta-model','model':name,'provider':os.getenv('WORLDTRACE_MODEL_PROVIDER','configured OpenAI-compatible endpoint'),'reason':str(obj.get('reason',''))[:350],'tasks':tasks}
    except Exception as ex:
        raise ModelUnavailable('Model planning failed: '+str(ex)[:350]) from ex
