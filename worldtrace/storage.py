import json, os, sqlite3, threading
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

LOCK = threading.RLock()
def utc(): return datetime.now(timezone.utc).isoformat()
def root():
    path=Path(os.getenv('WORLDTRACE_DATA_DIR','runtime')).resolve();path.mkdir(parents=True,exist_ok=True);return path

def connect():
    conn=sqlite3.connect(root()/'worldtrace.sqlite3',check_same_thread=False, timeout=15)
    conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('CREATE TABLE IF NOT EXISTS missions(id TEXT PRIMARY KEY, goal TEXT NOT NULL, status TEXT NOT NULL, created TEXT NOT NULL, updated TEXT NOT NULL, mode TEXT NOT NULL, error TEXT DEFAULT "")')
    conn.execute('CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, mission_id TEXT NOT NULL, time TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL, prev_hash TEXT NOT NULL, event_hash TEXT NOT NULL)')
    conn.execute('CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY, mission_id TEXT NOT NULL, name TEXT NOT NULL, tool TEXT NOT NULL, status TEXT NOT NULL, result TEXT NOT NULL DEFAULT "{}", ord INTEGER NOT NULL)')
    conn.execute('CREATE TABLE IF NOT EXISTS reviews(mission_id TEXT NOT NULL, tool TEXT NOT NULL, decision TEXT NOT NULL, reviewer TEXT NOT NULL, note TEXT NOT NULL, reviewed_at TEXT NOT NULL, PRIMARY KEY(mission_id,tool))')
    conn.execute('CREATE TABLE IF NOT EXISTS tool_runs(id TEXT PRIMARY KEY, tool TEXT NOT NULL, status TEXT NOT NULL, result TEXT NOT NULL, started TEXT NOT NULL, completed TEXT NOT NULL)')
    conn.commit();return conn

def make_mission(goal,mode):
    mid='WT-'+uuid4().hex[:10].upper()
    with LOCK, connect() as c:
        c.execute('INSERT INTO missions(id,goal,status,created,updated,mode) VALUES(?,?,?,?,?,?)',(mid,goal,'queued',utc(),utc(),mode))
    return mid

def update_mission(mid,status,error=''):
    with LOCK,connect() as c:c.execute('UPDATE missions SET status=?,updated=?,error=? WHERE id=?',(status,utc(),error,mid))

def add_task(mid,name,tool,order):
    tid='TASK-'+uuid4().hex[:10].upper()
    with LOCK,connect() as c:c.execute('INSERT INTO tasks(id,mission_id,name,tool,status,ord) VALUES(?,?,?,?,?,?)',(tid,mid,name,tool,'queued',order))
    return tid

def update_task(tid,status,result=None):
    with LOCK,connect() as c:c.execute('UPDATE tasks SET status=?,result=? WHERE id=?',(status,json.dumps(result or {},sort_keys=True,default=str),tid))

def event(mid,kind,payload):
    import hashlib
    data=json.dumps(payload,sort_keys=True,default=str,separators=(',',':'))
    with LOCK,connect() as c:
        r=c.execute('SELECT event_hash FROM events WHERE mission_id=? ORDER BY id DESC LIMIT 1',(mid,)).fetchone()
        prev=r['event_hash'] if r else 'GENESIS'
        stamp=utc(); h=hashlib.sha256(f'{mid}|{stamp}|{kind}|{data}|{prev}'.encode()).hexdigest()
        c.execute('INSERT INTO events(mission_id,time,kind,payload,prev_hash,event_hash) VALUES(?,?,?,?,?,?)',(mid,stamp,kind,data,prev,h))
    return h

def get(mid):
    with LOCK,connect() as c:
        m=c.execute('SELECT * FROM missions WHERE id=?',(mid,)).fetchone()
        if not m:return None
        ts=c.execute('SELECT * FROM tasks WHERE mission_id=? ORDER BY ord',(mid,)).fetchall()
        es=c.execute('SELECT * FROM events WHERE mission_id=? ORDER BY id',(mid,)).fetchall()
    return {**dict(m),'tasks':[{**dict(t),'result':json.loads(t['result'])} for t in ts],'events':[{**dict(e),'payload':json.loads(e['payload'])} for e in es]}

def record_review(mid, tool, decision, reviewer, note):
    '''Store a one-time human disposition of an existing recovery proposal; never execute it.'''
    with LOCK:
        mission = get(mid)
        if mission is None:
            raise ValueError('Mission not found')
        if mission['status'] != 'completed':
            raise ValueError('Mission must be completed before review')
        proposals = [p for e in mission['events'] if e['kind'] == 'recovery.proposed' for p in e['payload'].get('proposals', [])]
        if not any(p['tool'] == tool for p in proposals):
            raise ValueError('Tool has no proposed recovery action')
        stamp = utc()
        with connect() as c:
            if c.execute('SELECT 1 FROM reviews WHERE mission_id=? AND tool=?', (mid, tool)).fetchone():
                raise ValueError('Recovery proposal already reviewed')
            c.execute('INSERT INTO reviews VALUES(?,?,?,?,?,?)', (mid, tool, decision, reviewer, note, stamp))
        event(mid, 'recovery.reviewed', {'tool': tool, 'decision': decision, 'reviewer': reviewer, 'note': note, 'executed': False, 'reviewed_at': stamp})
        return {'mission_id': mid, 'tool': tool, 'decision': decision, 'reviewer': reviewer, 'note': note, 'executed': False, 'reviewed_at': stamp}

def reviews(mid):
    with LOCK, connect() as c:
        return [dict(row) for row in c.execute('SELECT * FROM reviews WHERE mission_id=? ORDER BY reviewed_at,tool', (mid,)).fetchall()]

def listing():
    with LOCK,connect() as c: return [dict(x) for x in c.execute('SELECT * FROM missions ORDER BY created DESC LIMIT 50').fetchall()]

def verify_chain(mid):
    import hashlib
    m=get(mid)
    if not m:return False
    prev='GENESIS'
    for e in m['events']:
        data=json.dumps(e['payload'],sort_keys=True,default=str,separators=(',',':'))
        h=hashlib.sha256(f"{mid}|{e['time']}|{e['kind']}|{data}|{prev}".encode()).hexdigest()
        if h!=e['event_hash'] or prev!=e['prev_hash']:return False
        prev=h
    return True


def record_tool_run(tool, status, result):
    """Persist a bounded standalone fixture-tool run for direct module workflows."""
    run_id = 'TR-' + uuid4().hex[:12].upper()
    stamp = utc()
    with LOCK, connect() as c:
        c.execute('INSERT INTO tool_runs(id,tool,status,result,started,completed) VALUES(?,?,?,?,?,?)',
                  (run_id,tool,status,json.dumps(result,sort_keys=True,default=str),stamp,stamp))
    return {'id':run_id,'tool':tool,'status':status,'result':result,'started':stamp,'completed':stamp,'source':'synthetic local fixture'}

def get_tool_run(run_id):
    with LOCK, connect() as c:
        row=c.execute('SELECT * FROM tool_runs WHERE id=?',(run_id,)).fetchone()
    if row is None:return None
    result=dict(row)
    result['result']=json.loads(result['result'])
    result['source']='synthetic local fixture'
    return result

def list_tool_runs(tool=None, limit=30):
    with LOCK, connect() as c:
        if tool:
            rows=c.execute('SELECT * FROM tool_runs WHERE tool=? ORDER BY started DESC LIMIT ?',(tool,limit)).fetchall()
        else:
            rows=c.execute('SELECT * FROM tool_runs ORDER BY started DESC LIMIT ?',(limit,)).fetchall()
    return [{**dict(row),'result':json.loads(row['result']),'source':'synthetic local fixture'} for row in rows]
