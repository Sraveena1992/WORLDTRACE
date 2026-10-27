"""Bounded, real local tool implementations; no pretend integrations."""
import csv, json, sqlite3, time, hashlib, email
from pathlib import Path
from collections import Counter
from pypdf import PdfReader
from .storage import root

TOOL_INFO=[
 {'id':'pdf_inspect','title':'PDF intelligence','domain':'Document QA','access':'local read'},
 {'id':'email_inspect','title':'Email automation','domain':'Mail validation','access':'local read'},
 {'id':'network_inspect','title':'Network observability','domain':'HAR analysis','access':'local read'},
 {'id':'etl_compare','title':'ETL verification','domain':'Data integrity','access':'local read'},
 {'id':'database_check','title':'Database testing','domain':'SQL assertions','access':'read only'},
 {'id':'api_virtualize','title':'API virtualization','domain':'Mock contract','access':'local mock'},
 {'id':'performance_probe','title':'Performance probe','domain':'Shift-left testing','access':'local bounded'},
 {'id':'middleware_test','title':'Middleware testing','domain':'Queue replay','access':'local mock'},
 {'id':'mainframe_contract','title':'Mainframe contract','domain':'Record validation','access':'local fixture'},
]
AVAILABLE={x['id'] for x in TOOL_INFO}

def safe_path(name):
    base=(root()/'samples').resolve();base.mkdir(exist_ok=True)
    p=(base/name).resolve()
    if not p.is_relative_to(base):raise ValueError('Path outside approved sample workspace')
    return p

def pdf_inspect():
    p=safe_path('supplier_check.pdf');reader=PdfReader(str(p));txt='\n'.join(page.extract_text() or '' for page in reader.pages)
    checks={'supplier_name': 'NORTHSTAR COMPONENTS' in txt.upper(),'signed': 'SIGNED: YES' in txt.upper(),'tax_id': 'TAX ID:' in txt.upper()}
    return {'file':p.name,'pages':len(reader.pages),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'checks':checks,'pass':all(checks.values()),'excerpt':txt[:420]}

def email_inspect():
    p=safe_path('supplier_notice.eml');msg=email.message_from_bytes(p.read_bytes());subject=msg.get('Subject','');body=msg.get_payload(decode=True)
    if isinstance(body,bytes):body=body.decode(errors='replace')
    ok='onboarding' in subject.lower() and 'missing' in str(body).lower()
    return {'file':p.name,'subject':subject,'sender':msg.get('From'),'checks':{'mentions_onboarding': 'onboarding' in subject.lower(),'reports_missing': 'missing' in str(body).lower()},'pass':ok}

def network_inspect():
    p=safe_path('network.har');data=json.loads(p.read_text());entries=data.get('log',{}).get('entries',[])
    failures=[{'url':x.get('request',{}).get('url',''),'status':x.get('response',{}).get('status'),'ms':x.get('time')} for x in entries if int(x.get('response',{}).get('status',200))>=400]
    return {'total_requests':len(entries),'failure_count':len(failures),'failures':failures,'pass':not failures,'finding':'HTTP failures detected' if failures else 'No HTTP failures in supplied sample'}

def etl_compare():
    def read(n):
        with safe_path(n).open(newline='') as f:return {r['id']:r for r in csv.DictReader(f)}
    src=read('source.csv');target=read('target.csv')
    missing=sorted(set(src)-set(target));mismatched=sorted(k for k in src.keys()&target.keys() if src[k]!=target[k]);extra=sorted(set(target)-set(src))
    return {'source_rows':len(src),'target_rows':len(target),'missing_ids':missing,'mismatched_ids':mismatched,'extra_ids':extra,'pass':not(missing or mismatched or extra)}

def database_check():
    uri=f"file:{safe_path('supplier.db')}?mode=ro";c=sqlite3.connect(uri,uri=True)
    try:
        cnt=c.execute('SELECT COUNT(*) FROM suppliers').fetchone()[0]
        pending=c.execute("SELECT COUNT(*) FROM suppliers WHERE status='PENDING'").fetchone()[0]
    finally:c.close()
    return {'table':'suppliers','rows':cnt,'pending':pending,'pass':pending==0,'access':'read-only SQL on approved sample database'}

def api_virtualize():
    p=safe_path('contract.json');contract=json.loads(p.read_text());expected=contract['expected_status'];mock=contract['simulated_status'];return {'endpoint':contract['endpoint'],'expected':expected,'simulated':mock,'pass':expected==mock,'mode':'local mock; no external API called'}

def performance_probe():
    values=[]
    for _ in range(20):
        t=time.perf_counter();hashlib.sha256(b'WORLDTRACE-BENCHMARK'*100).digest();values.append((time.perf_counter()-t)*1000)
    values.sort();return {'samples':20,'p95_ms':round(values[int(.95*(len(values)-1))],4),'pass':values[-1]<100,'target':'bounded in-process hashing only; not production service throughput'}

def middleware_test():
    messages=json.loads(safe_path('messages.json').read_text());ids=[m['id'] for m in messages]
    return {'messages':len(messages),'unique_ids':len(set(ids)),'duplicates':sorted(k for k,v in Counter(ids).items() if v>1),'pass':len(ids)==len(set(ids)),'mode':'local queue-fixture replay, not broker connected'}

def mainframe_contract():
    lines=safe_path('mainframe.txt').read_text().splitlines();invalid=[i+1 for i,line in enumerate(lines) if len(line)!=20 or not line[:6].isdigit()]
    return {'records':len(lines),'invalid_lines':invalid,'pass':not invalid,'mode':'fixed-width file contract; not connected to actual mainframe'}

FUNCTIONS={name:globals()[name] for name in AVAILABLE}
def execute(name):
    if name not in FUNCTIONS:raise ValueError('Tool not allowlisted')
    return FUNCTIONS[name]()
