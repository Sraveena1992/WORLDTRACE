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
