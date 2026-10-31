"""Public, synthetic-only supplier resolution demonstration.

No user uploads, external system calls, real secrets or production writes.
Each randomized capability token refers to a TTL-bounded isolated in-memory
SQLite instance. The visitor must explicitly approve before execution.
"""
import hashlib
import json
import secrets
import sqlite3
import threading
import time
from datetime import datetime, timezone
from . import multifile

LOCK=threading.RLock()
SESSIONS={}
TTL_SECONDS=1200
MAX_SESSIONS=40

def _utc():return datetime.now(timezone.utc).isoformat()
def _digest(payload):return hashlib.sha256(payload.encode()).hexdigest()

def _clean():
    now=time.time()
    for key,s in list(SESSIONS.items()):
        if s["expires"]<=now:
            s["db"].close()
            del SESSIONS[key]

def _get(token):
    if not token or len(token)>100 or token not in SESSIONS:
        raise ValueError("Demo session not found or expired")
    s=SESSIONS[token]
    if s["expires"]<=time.time():
        s["db"].close()
        del SESSIONS[token]
        raise ValueError("Demo session expired")
    return s

def _snapshot(conn):
    return {r[0]:r[1] for r in conn.execute("SELECT record_key,row_digest FROM target_rows")}

def _view(token,s):
    current=_snapshot(s["db"])
    verified=s["status"]=="VERIFIED_SANDBOX"
    return {"demo_id":token,"status":s["status"],"expires_seconds":max(0,int(s["expires"]-time.time())),
        "synthetic_only":True,"requires_private_token":False,
        "instruction":s["analysis"]["goal"],"observations":s["analysis"]["observations"],
        "trace":s["trace"],"trace_verified":multifile.verify_trace(s["trace"]),
        "report_sha256":s["analysis"]["report_sha256"],
        "proposed_actions":s["analysis"]["proposed_actions"],
        "missing_ids":["A3"],"source_rows":len(s["source"]),
        "initial_target_rows":len(s["initial"]),"current_target_rows":len(current),
        "approved":s["approved"],"approval_time":s["approved_at"],
        "verified":verified,"before_sha256":s["before_digest"],
        "after_sha256":_digest(json.dumps(current,sort_keys=True)) if verified else None,
        "rows_added":len(s["source"])-len(s["initial"]) if verified else 0,
        "external_writes":0,"original_csv_modified":False,
        "scope":"Synthetic session / in-memory SQLite only. No Meta inference or production changes."}

def start():
    with LOCK:
        _clean()
        if len(SESSIONS)>=MAX_SESSIONS:
            raise RuntimeError("Demo capacity reached; try again after earlier sessions expire")
        token=secrets.token_urlsafe(24)
        salt=secrets.token_hex(16)
        goal="Investigate missing supplier onboarding records, require human approval, repair an isolated demo copy and independently verify."
        raw_source=b"id,name\nA1,Alpha\nA2,Beta\nA3,Gamma\n"
        raw_target=b"id,name\nA1,Alpha\nA2,Beta\n"
        analysis=multifile.run(goal,{"source_csv":("synthetic-source.csv",raw_source),
                                     "target_csv":("synthetic-target.csv",raw_target)})
        def hash_records(raw):
            import csv
            import io
            rows=csv.DictReader(io.StringIO(raw.decode()))
            return {_digest(salt+":id:"+row["id"]):_digest(salt+":row:"+json.dumps(row,sort_keys=True))
                    for row in rows}
        source=hash_records(raw_source);target=hash_records(raw_target)
        db=sqlite3.connect(":memory:",check_same_thread=False)
        db.execute("CREATE TABLE target_rows(record_key TEXT PRIMARY KEY,row_digest TEXT NOT NULL)")
        db.executemany("INSERT INTO target_rows VALUES(?,?)",target.items())
        db.commit()
        SESSS={"db":db,"expires":time.time()+TTL_SECONDS,"source":source,"initial":target,
               "analysis":analysis,"status":"REVIEW_NEEDED","approved":False,
               "approved_at":None,"trace":list(analysis["trace"]),
               "before_digest":_digest(json.dumps(target,sort_keys=True))}
        SESSIONS[token]=SESSS
        return _view(token,SESSS)

def get(token):
    with LOCK:
        _clean()
        return _view(token,_get(token))

def approve(token):
    with LOCK:
        s=_get(token)
        if s["status"]!="REVIEW_NEEDED":
            raise ValueError("Demo can only be approved once")
        s["approved"]=True
        s["approved_at"]=_utc()
        s["status"]="APPROVED_SANDBOX_ONLY"
        multifile._event(s["trace"],"Human Review","explicit_demo_approval",
              {"scope":"in-memory SQLite synthetic records only","external_actions":0})
        return _view(token,s)

def execute(token):
    with LOCK:
        s=_get(token)
        if not s["approved"] or s["status"]!="APPROVED_SANDBOX_ONLY":
            raise ValueError("Explicit demo approval required; completed demos cannot be replayed")
        desired=s["source"]
        conn=s["db"]
        before=_snapshot(conn)
        if before!=s["initial"]:
            raise ValueError("Demo baseline changed, correction rejected")
        missing=set(desired)-set(before)
        if not missing or set(before)-set(desired) or any(before[k]!=desired[k] for k in before):
            raise ValueError("Only missing rows may be inserted into isolated demo")
        with conn:
            for key in sorted(missing):
                conn.execute("INSERT INTO target_rows VALUES(?,?)",(key,desired[key]))
            after=_snapshot(conn)
            if after!=desired:
                raise ValueError("Reverification failed; correction rolled back")
        s["status"]="VERIFIED_SANDBOX"
        multifile._event(s["trace"],"Execution Agent","approved_sqlite_sandbox_insert",
              {"rows_added":len(missing),"before_count":len(before),"after_count":len(after),"external_writes":0})
        multifile._event(s["trace"],"Verification Agent","independently_requery_sqlite",
              {"actual_equal_expected":True,"state_sha256":_digest(json.dumps(after,sort_keys=True))})
        return _view(token,s)
