"""Readable evidence and domain-appropriate uploaded PDF analysis."""
from pathlib import Path
from worldtrace import uploads

def test_generic_pdf_passes_without_supplier_tax_id():
    from reportlab.pdfgen.canvas import Canvas
    import io
    buffer=io.BytesIO()
    c=Canvas(buffer)
    c.drawString(60,750,"Introduction to AI agents and document workflows")
    c.save()
    result=uploads.inspect("pdf_inspect","AI-guide.pdf",buffer.getvalue())
    assert result["status"]=="passed"
    assert result["result"]["checks"]["has_text"] is True
    assert result["result"]["checks"]["mentions_tax_id"] is False
    assert result["result"]["document_type"]=="general_pdf"

def test_results_have_plain_language_noninteractive_status():
    base=Path(__file__).resolve().parents[1]/"static"
    js=(base/"app.js").read_text(encoding="utf8")
    css=(base/"style.css").read_text(encoding="utf8")
    html=(base/"index.html").read_text(encoding="utf8")
    assert "function evidenceCard(" in js
    assert "function resultExplanation(" in js
    assert "status; not a button" in js
    assert "evidenceCard(data.tool,result,'upload'" in js
    assert "evidenceCard(run.tool,result,'fixture'" in js
    assert ".human-result-head" in css
    assert '/assets/app.js?v=23' in html
