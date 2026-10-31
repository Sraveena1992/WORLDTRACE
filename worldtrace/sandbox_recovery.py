"""Bounded, human-approved repair of an isolated SQLite demo snapshot.

Never changes source CSVs, production databases, or external systems.
Stores salted hashes of records, not raw uploaded business rows.
"""
import hashlib
import json
from . import storage

def _tables(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS demo_target_records (
       mission_id TEXT NOT NULL, record_key TEXT NOT NULL,
       row_hash TEXT NOT NULL, PRIMARY KEY(mission_id, record_key))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS demo_execution (
       mission_id TEXT NOT NULL, action_index INTEGER NOT NULL,
       executed_at TEXT NOT NULL, added_records INTEGER NOT NULL,
       before_count INTEGER NOT NULL, after_count INTEGER NOT NULL,
       verified INTEGER NOT NULL, before_digest TEXT NOT NULL,
       after_digest TEXT NOT NULL, PRIMARY KEY(mission_id, action_index))""")

def initialize(conn, mission_id, result):
    """Initialize a sandbox from hashed target records during opt-in save."""
    snapshot=result.get("demo_repair")
    if not snapshot or snapshot.get("kind")!="isolated_sqlite_csv_reconciliation":
        return
    _tables(conn)
    for key,value in snapshot["target"].items():
        conn.execute("INSERT INTO demo_target_records VALUES(?,?,?)",(mission_id,key,value))

def _digest(records):
    canonical=json.dumps(records,sort_keys=True,separators=(",",":"))
    return hashlib.sha256(canonical.encode()).hexdigest()

def history(mission_id):
    with storage.LOCK, storage.connect() as conn:
        _tables(conn)
        return [dict(row) for row in conn.execute(
            "SELECT * FROM demo_execution WHERE mission_id=? ORDER BY executed_at",
            (mission_id,)).fetchall()]

def execute(mission_id,action_index):
    """Execute only the exact previously approved reconciliation on sandbox rows."""
    if not isinstance(action_index,int) or isinstance(action_index,bool) or action_index<0:
        raise ValueError("Invalid action index")
    with storage.LOCK, storage.connect() as conn:
        _tables(conn)
        # IMMEDIATE locks writes and prevents parallel approvals/executions racing.
        conn.execute("BEGIN IMMEDIATE")
        row=conn.execute("SELECT result_json FROM unified_records WHERE id=?",(mission_id,)).fetchone()
        if row is None:
            raise ValueError("Mission not found")
        result=json.loads(row["result_json"])
        actions=result.get("proposed_actions",[])
        if action_index>=len(actions) or actions[action_index].get("type")!="sandbox_csv_reconcile":
            raise ValueError("No executable sandbox correction for this action")
        review=conn.execute("SELECT decision FROM unified_decisions WHERE mission_id=? AND action_index=?",
                            (mission_id,action_index)).fetchone()
        if review is None or review["decision"]!="approve_manual_followup":
            raise ValueError("Explicit human approval for manual follow-up is required")
        if conn.execute("SELECT 1 FROM demo_execution WHERE mission_id=? AND action_index=?",
                        (mission_id,action_index)).fetchone():
            raise ValueError("Sandbox correction already executed")
        snapshot=result.get("demo_repair")
        if not snapshot:
            raise ValueError("No isolated demo state available")
        desired=snapshot["source"]
        initial=snapshot["target"]
        before={r["record_key"]:r["row_hash"] for r in conn.execute(
            "SELECT record_key,row_hash FROM demo_target_records WHERE mission_id=?",(mission_id,))}
        if before!=initial:
            raise ValueError("Sandbox baseline changed; refuse unsafe replay")
        missing=set(desired)-set(before)
        if not missing:
            raise ValueError("No missing rows to repair")
        # Prevent claiming a complete fix where other differences remain.
        if set(before)-set(desired) or any(before[k]!=desired[k] for k in set(before)&set(desired)):
            raise ValueError("Mismatch/extra rows require separate intervention; no automatic fix")
        for key in sorted(missing):
            conn.execute("INSERT INTO demo_target_records VALUES(?,?,?)",
                         (mission_id,key,desired[key]))
        after={r["record_key"]:r["row_hash"] for r in conn.execute(
            "SELECT record_key,row_hash FROM demo_target_records WHERE mission_id=?",(mission_id,))}
        verified=after==desired
        if not verified:
            raise ValueError("Post-execution verification failed; transaction rolled back")
        now=storage.utc()
        before_hash,after_hash=_digest(before),_digest(after)
        conn.execute("INSERT INTO demo_execution VALUES(?,?,?,?,?,?,?,?,?)",
             (mission_id,action_index,now,len(missing),len(before),len(after),
              1,before_hash,after_hash))
        return {"mission_id":mission_id,"action_index":action_index,
                "execution":"ISOLATED_SQLITE_SANDBOX_ONLY","executed":True,
                "verified":True,"rows_added":len(missing),"before_count":len(before),
                "after_count":len(after),"before_sha256":before_hash,
                "after_sha256":after_hash,"executed_at":now,
                "external_writes":0,"original_csv_modified":False}
