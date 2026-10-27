import csv,json,sqlite3
from email.message import EmailMessage
from pathlib import Path
from reportlab.pdfgen import canvas
from .storage import root

def ensure():
    p=root()/'samples';p.mkdir(exist_ok=True)
    pdf=p/'supplier_check.pdf'
    if not pdf.exists():
        c=canvas.Canvas(str(pdf),pagesize=(612,792));c.setFont('Helvetica-Bold',16);c.drawString(45,730,'Supplier Onboarding Compliance Record');c.setFont('Helvetica',11)
        for idx,line in enumerate(['SUPPLIER NAME: NORTHSTAR COMPONENTS','TAX ID: NS-39012','SIGNED: NO','DOCUMENT STATUS: INCOMPLETE']):c.drawString(45,680-idx*25,line)
        c.save()
    em=p/'supplier_notice.eml'
    if not em.exists():
        msg=EmailMessage();msg['From']='vendor@example.test';msg['To']='ops@example.test';msg['Subject']='Supplier onboarding documentation';msg.set_content('The compliance signature is missing. Please request a signed document.');em.write_bytes(msg.as_bytes())
    har=p/'network.har'
    if not har.exists():har.write_text(json.dumps({'log':{'entries':[{'request':{'url':'https://example.test/api/suppliers'},'response':{'status':200},'time':45},{'request':{'url':'https://example.test/api/validate'},'response':{'status':503},'time':2100}]}},indent=2))
    for name,rows in [('source.csv',[['id','status'],['A01','READY'],['A02','READY'],['A03','PENDING']]),('target.csv',[['id','status'],['A01','READY'],['A02','READY']])]:
        if not (p/name).exists():
            with (p/name).open('w',newline='') as f:csv.writer(f).writerows(rows)
    db=p/'supplier.db'
    if not db.exists():
        with sqlite3.connect(db) as conn:
            conn.execute('CREATE TABLE suppliers(id TEXT PRIMARY KEY,status TEXT)');conn.executemany('INSERT INTO suppliers VALUES (?,?)',[('A01','READY'),('A02','PENDING')])
    files={'contract.json':{'endpoint':'/api/onboarding/validate','expected_status':200,'simulated_status':503},'messages.json':[{'id':'evt-001','status':'ok'},{'id':'evt-001','status':'retry'}]}
    for fname,data in files.items():
        if not (p/fname).exists():(p/fname).write_text(json.dumps(data,indent=2))
    mf=p/'mainframe.txt'
    if not mf.exists():mf.write_text('000001SUPPLIER-VALID   \n000002SUPPLIER-CHECK   \n')
