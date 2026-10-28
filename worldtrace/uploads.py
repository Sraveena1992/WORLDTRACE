"""Safe in-memory analysis of user-provided files; no external writes or model calls."""
import csv
import email
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from pypdf import PdfReader

MAX_BYTES=2*1024*1024
FORMATS={
    "pdf_inspect":(".pdf",),
    "email_inspect":(".eml",),
    "network_inspect":(".har",),
    "etl_compare":(".csv",),
    "api_virtualize":(".json",),
    "middleware_test":(".json",),
    "mainframe_contract":(".txt",),
}
def _csv_rows(payload):
    decoded=payload.decode("utf-8-sig")
    rows=list(csv.DictReader(io.StringIO(decoded)))
    if not rows or "id" not in (rows[0] or {}):
        raise ValueError("CSV must have an id header and at least one row")
    if len(rows)>10000 or any(not r.get("id") for r in rows):
        raise ValueError("CSV has too many rows or blank IDs")
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("CSV contains duplicate IDs")
    return {r["id"]:r for r in rows}

def inspect(tool, filename, payload, comparison=None):
    """Data is never interpreted as executable code or sent to outside systems."""
    if tool not in FORMATS:raise ValueError("This tool does not support uploads")
    suffix=Path(filename).suffix.lower()
    if suffix not in FORMATS[tool]:raise ValueError("Incorrect file type for selected tool")
    if not payload or len(payload)>MAX_BYTES:raise ValueError("File must be 1 byte to 2 MiB")
    digest=hashlib.sha256(payload).hexdigest()
    if tool=="pdf_inspect":
        reader=PdfReader(io.BytesIO(payload))
        if len(reader.pages)>50:raise ValueError("PDF limited to 50 pages")
        text="\n".join(page.extract_text() or "" for page in reader.pages)[:100000]
        checks={"has_text":bool(text.strip()),"mentions_signature":("signature" in text.lower() or "signed" in text.lower()),"mentions_tax_id":"tax id" in text.lower()}
        result={"pages":len(reader.pages),"characters":len(text),"checks":checks,"excerpt":text[:400],"pass":all(checks.values())}
    elif tool=="email_inspect":
        msg=email.message_from_bytes(payload)
        subject=str(msg.get("Subject",""))[:200]
        sender=str(msg.get("From",""))[:200]
        result={"sender":sender,"subject":subject,"has_subject":bool(subject),"has_sender":bool(sender),"pass":bool(subject and sender)}
    elif tool=="network_inspect":
        data=json.loads(payload.decode("utf-8-sig"))
        entries=data.get("log",{}).get("entries",[])
        if not isinstance(entries,list) or len(entries)>5000:raise ValueError("Invalid HAR entries")
        failures=[{"status":e.get("response",{}).get("status"),"url":str(e.get("request",{}).get("url",""))[:200]} for e in entries if isinstance(e,dict) and isinstance(e.get("response"),dict) and isinstance(e.get("response",{}).get("status"),int) and e["response"]["status"]>=400]
        result={"total_requests":len(entries),"failure_count":len(failures),"failures":failures[:20],"pass":not failures}
    elif tool=="etl_compare":
        if comparison is None:raise ValueError("Source CSV and target CSV are required")
        if len(comparison)>MAX_BYTES:raise ValueError("Target file exceeds 2 MiB")
        source=_csv_rows(payload);target=_csv_rows(comparison)
        missing=sorted(source.keys()-target.keys())
        extra=sorted(target.keys()-source.keys())
        mismatch=sorted(k for k in source.keys()&target.keys() if source[k]!=target[k])
        result={"source_rows":len(source),"target_rows":len(target),"missing_ids":missing[:100],"extra_ids":extra[:100],"mismatched_ids":mismatch[:100],"pass":not(missing or extra or mismatch)}
    elif tool=="api_virtualize":
        data=json.loads(payload.decode("utf-8-sig"))
        expected=data.get("expected_status");observed=data.get("simulated_status")
        if not isinstance(expected,int) or not isinstance(observed,int):raise ValueError("JSON requires integer expected_status and simulated_status")
        result={"expected_status":expected,"simulated_status":observed,"pass":expected==observed,"note":"JSON contract check only; no network calls"}
    elif tool=="middleware_test":
        data=json.loads(payload.decode("utf-8-sig"))
        if not isinstance(data,list) or len(data)>10000 or any(not isinstance(x,dict) or "id" not in x for x in data):
            raise ValueError("JSON must be an array of messages with id")
        counts=Counter(str(x["id"]) for x in data)
        duplicates=sorted(k for k,v in counts.items() if v>1)
        result={"messages":len(data),"duplicates":duplicates[:100],"pass":not duplicates}
    else:
        lines=payload.decode("utf-8-sig").splitlines()
        if len(lines)>10000:raise ValueError("Too many records")
        invalid=[i for i,line in enumerate(lines,1) if len(line)!=20 or not line[:6].isdigit()]
        result={"records":len(lines),"invalid_lines":invalid[:100],"pass":not invalid}
    return {"tool":tool,"file_name":Path(filename).name[:120],"sha256":digest,
            "source":"USER_UPLOADED_FILE","result":result,"status":"passed" if result["pass"] else "finding",
            "limitations":"Local parser only; not AI inference or external verification"}
