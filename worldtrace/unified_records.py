"""Private operator-only completed mission records and review decisions.

Opt-in persisted results are SQLite-backed; no raw uploads are stored. Records
are not durable across ephemeral Render filesystem resets.
"""
import hashlib
import json
import re
import sqlite3
from uuid import uuid4
from . import storage, sandbox_recovery

ID_PATTERN=re.compile(r"UM-[0-9A-F]{16}$")

def _db():
    conn=storage.connect()
    conn.execute("""CREATE TABLE IF NOT EXISTS unified_records (
        id TEXT PRIMARY KEY, created TEXT NOT NULL, goal TEXT NOT NULL,
        status TEXT NOT NULL, result_json TEXT NOT NULL,
        report TEXT NOT NULL, report_sha256 TEXT NOT NULL)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS unified_decisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, mission_id TEXT NOT NULL,
        action_index INTEGER NOT NULL, decision TEXT NOT NULL,
        reviewer TEXT NOT NULL, note TEXT NOT NULL, created TEXT NOT NULL,
        UNIQUE(mission_id, action_index))""")
    conn.commit()
    return conn

def record(result):
    """Explicit opt-in to persist derived findings and report, not source files."""
    mid="UM-"+uuid4().hex[:16].upper()
    created=storage.utc()
    payload={k:v for k,v in result.items() if k!="report_markdown"}
    with storage.LOCK,_db() as conn:
        conn.execute("INSERT INTO unified_records VALUES(?,?,?,?,?,?,?)",
            (mid,created,result["goal"],result["status"],
             json.dumps(payload,ensure_ascii=False),result["report_markdown"],result["report_sha256"]))
        sandbox_recovery.initialize(conn,mid,result)
    return {"id":mid,"created":created,"stored":True}

def _check_id(mid):
    if not ID_PATTERN.fullmatch(mid):
        raise ValueError("Mission not found")

def listing():
    with storage.LOCK,_db() as conn:
        rows=conn.execute("SELECT id,created,goal,status,report_sha256 FROM unified_records ORDER BY created DESC LIMIT 30").fetchall()
        return [dict(r) for r in rows]

def get(mid):
    _check_id(mid)
    with storage.LOCK,_db() as conn:
        row=conn.execute("SELECT * FROM unified_records WHERE id=?",(mid,)).fetchone()
        if row is None:raise ValueError("Mission not found")
        result=json.loads(row["result_json"])
        return {"id":mid,"created":row["created"],**result,
                "report_markdown":row["report"],"report_sha256":row["report_sha256"],
                "decisions":decisions(mid), "sandbox_executions":sandbox_recovery.history(mid)}

def decisions(mid):
    _check_id(mid)
    with storage.LOCK,_db() as conn:
        return [dict(x) for x in conn.execute("SELECT action_index,decision,reviewer,note,created FROM unified_decisions WHERE mission_id=? ORDER BY action_index",(mid,))]

def decide(mid,action_index,decision,reviewer,note=""):
    _check_id(mid)
    if decision not in ("approve_manual_followup","reject"):raise ValueError("Invalid review decision")
    if not isinstance(action_index,int) or isinstance(action_index,bool) or action_index<0:raise ValueError("Invalid action index")
    if not 2<=len(reviewer.strip())<=80 or len(note)>500:raise ValueError("Invalid reviewer details")
    with storage.LOCK,_db() as conn:
        row=conn.execute("SELECT result_json FROM unified_records WHERE id=?",(mid,)).fetchone()
        if row is None:raise ValueError("Mission not found")
        actions=json.loads(row["result_json"]).get("proposed_actions",[])
        if action_index>=len(actions):raise ValueError("Action not found")
        try:
            conn.execute("INSERT INTO unified_decisions(mission_id,action_index,decision,reviewer,note,created) VALUES(?,?,?,?,?,?)",
                (mid,action_index,decision,reviewer.strip(),note,storage.utc()))
        except sqlite3.IntegrityError as exc:raise ValueError("Action already reviewed") from exc
    return {"mission_id":mid,"action_index":action_index,"decision":decision,
            "executed":False,"message":"Decision recorded only; no external action was executed"}
