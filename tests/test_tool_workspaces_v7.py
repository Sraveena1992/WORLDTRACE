"""Standalone specialist workspaces: real bounded fixture execution and persistence."""
from fastapi.testclient import TestClient
from pathlib import Path
import app
from worldtrace import samples, tools

client=TestClient(app.app)

def test_each_specialist_has_independent_workspace_and_run():
    samples.ensure()
    for name in sorted(tools.AVAILABLE):
        info=client.get(f"/api/tools/{name}/workspace")
        assert info.status_code==200, (name,info.text)
        details=info.json()
        assert details["fixture"] and len(details["steps"])>=4
        response=client.post(f"/api/tools/{name}/runs")
        assert response.status_code==201,(name,response.text)
        run=response.json()
        assert run["tool"]==name
        assert run["status"] in ("passed","finding")
        assert run["source"]=="synthetic local fixture"
        assert run["result"] == tools.execute(name) if name != "performance_probe" else "p95_ms" in run["result"]
        saved=client.get("/api/tool-runs/"+run["id"])
        assert saved.status_code==200
        assert saved.json()["tool"]==name
        history=client.get(f"/api/tools/{name}/runs")
        assert history.status_code==200
        assert any(item["id"]==run["id"] for item in history.json())

def test_unknown_tool_cannot_run():
    assert client.post("/api/tools/not_allowlisted/runs").status_code==404
    assert client.get("/api/tools/not_allowlisted/workspace").status_code==404
    assert client.get("/api/tools/not_allowlisted/runs").status_code==404

def test_workspace_cards_do_not_redirect_to_mission_composer():
    js=(Path(__file__).resolve().parents[1]/"static"/"app.js").read_text(encoding="utf-8")
    assert "async function launchTool(tool)" in js
    assert "route('workspace')" in js
    assert "api('/api/tools/'+encodeURIComponent(app.workspaceTool)+'/runs',{method:'POST'})" in js
    assert "loadToolHistory()" in js
    html=(Path(__file__).resolve().parents[1]/"static"/"index.html").read_text(encoding="utf-8")
    assert 'id="workspace" class="page"' in html
    assert 'id="runOneTool"' in html
    assert 'id="workspaceResult"' in html
