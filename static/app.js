const $=id=>document.getElementById(id);
const app={mode:'local',active:null,timer:null,missions:[],tools:[],missionToken:null,workspaceTool:null,workspaceSource:'tools',unifiedMissions:[],selectedUnified:null};
function safe(t){return String(t??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
async function api(path,opt){const r=await fetch(path,opt);let data;try{data=await r.json()}catch{data={detail:`HTTP ${r.status}`}}if(!r.ok)throw Error(typeof data.detail==='string'?data.detail:`HTTP ${r.status}`);return data}
function route(name){document.querySelectorAll('.page').forEach(e=>e.classList.toggle('shown',e.id===name));document.querySelectorAll('[data-route]').forEach(e=>e.classList.toggle('active',e.dataset.route===name));$('crumb').textContent={overview:'MISSION CONTROL',agents:'AGENT WORKFORCE',tools:'ENTERPRISE TOOLS',audit:'EVIDENCE LEDGER',reviews:'HUMAN REVIEW',workspace:'SPECIALIST WORKSPACE',deliverables:'OUTCOME STUDIO',multi:'MULTI-FILE MISSION'}[name];window.scrollTo({top:0,behavior:'smooth'});if(name==='reviews')renderReviewQueue();if(name==='agents')renderAgentWorkforce();if(name==='audit'&&app.active){$('auditMission').value=app.active;showAudit(app.active)}}
for(const b of document.querySelectorAll('[data-route]'))b.addEventListener('click',()=>route(b.dataset.route));
$('topNewMission').onclick=()=>route('multi');$('openUnifiedMission').onclick=()=>route('multi');$('jumpReview').onclick=()=>route('reviews');$('refreshReviews').onclick=()=>refresh();$('focusGoal').onclick=()=>route('multi');$('jumpWorkflow').onclick=()=>route('tools');$('refresh').onclick=async()=>{
 const status=$('fixtureRefreshStatus');
 status.textContent='Reloading legacy sample history…';
 await refresh();
 status.textContent='Fixture history refreshed. '+app.missions.length+
  ' WT- mission(s) currently recorded. This does not load public demo or UM- mission records.';
};
function setMode(mode){app.mode=mode;$('modeLocal').classList.toggle('selected',mode==='local');$('modeModel').classList.toggle('selected',mode==='model');$('modeInfo').innerHTML=mode==='local'?'Local mode uses deterministic keyword routing on synthetic fixtures. It is <strong>not</strong> AI-generated planning.':'Model mode calls your configured Meta-compatible endpoint to select tools and create the mission plan. It requires real working credentials.'}
$('modeLocal').onclick=()=>setMode('local');$('modeModel').onclick=()=>setMode('model');
const toolAgents={'pdf_inspect':['◫','Document Analyst','Reads PDF and checks factual fields against defined assertions.'],'email_inspect':['✉','Communications Analyst','Validates real local email message content and expected signals.'],'network_inspect':['⌁','Network Investigator','Inspects a supplied HAR capture and identifies failed requests.'],'etl_compare':['⇄','Data Integrity Agent','Compares source and target records and flags divergences.'],'database_check':['▥','Database Auditor','Runs bounded read-only assertions on an approved sample database.'],'api_virtualize':['⟐','API Simulator','Validates API contract expectations using local mock responses.'],'performance_probe':['◷','Performance Engineer','Executes a bounded, repeatable in-process latency check.'],'middleware_test':['⊞','Integration Tester','Replays fixture message IDs and checks for duplicates.'],'mainframe_contract':['▤','Legacy Systems Analyst','Validates fixed-width record contracts; no actual mainframe access.']};
function renderCapabilities(cap){app.tools=cap.tools;$('metricModel').innerHTML=cap.model_mode_available?'CHECK<span class="metric-unit">MODEL</span>':'OFF<span class="metric-unit">line</span>';$('modelFoot').textContent=cap.model_mode_available?'Credentials configured; inference NOT yet verified':'Model endpoint not configured';let cards='',agents='';cap.tools.forEach((t,i)=>{const role=toolAgents[t.id]||['◈',t.title,t.domain];cards+=`<article class="tool-card interactive-card" tabindex="0" role="button" data-launch-tool="${safe(t.id)}" aria-label="Run synthetic ${safe(t.title)} workflow"><span class="tool-number">${String(i+1).padStart(2,'0')}</span><div class="category">${safe(t.domain).toUpperCase()}</div><h3>${safe(t.title)}</h3><p>${safe(role[2])}</p><div class="mini-status">● ${safe(t.access).toUpperCase()} · TEST FIXTURE</div></article>`;});$('toolGrid').innerHTML=cards;renderAgentWorkforce();document.querySelectorAll('[data-launch-tool]').forEach(el=>{const action=()=>launchTool(el.dataset.launchTool);el.addEventListener('click',action);el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();action()}})})}
function fmt(st){return st==='completed'?'COMPLETED':st.toUpperCase()}
function historyRow(m){return `<div class="history-row"><div style="min-width:0"><div class="history-id">${safe(m.id)} <span class="muted">/ ${safe(m.mode).toUpperCase()}</span></div><div class="history-goal" title="${safe(m.goal)}">${safe(m.goal)}</div></div><div class="history-actions"><span class="status ${safe(m.status)}">${fmt(m.status)}</span><button class="tiny-btn" data-view="${safe(m.id)}">Inspect</button>${m.status==='completed'?`<a class="report-btn" href="/api/missions/${encodeURIComponent(m.id)}/report">↓ Report</a>`:''}</div></div>`}
async function refresh(){try{const list=await api('/api/missions');app.missions=list;$('metricMissions').textContent=list.length;$('missionHistory').innerHTML=list.length?list.map(historyRow).join(''):'<div class="muted">No missions yet.</div>';const auditSelection=$('auditMission').value;$('auditMission').innerHTML='<option value="">Select a mission</option>'+list.map(m=>`<option value="${safe(m.id)}">${safe(m.id)} — ${safe(m.status)}</option>`).join('');$('auditMission').value=auditSelection;document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{route('overview');showMission(b.dataset.view)});renderReviewQueue();}catch(e){$('connection').textContent='● API UNAVAILABLE';$('error').hidden=false;$('error').textContent=e.message}}
function describeEvent(e){if(e.kind==='tool.completed'){const p=e.payload;return `${p.tool}: ${p.status.toUpperCase()} · ${JSON.stringify(p.result).slice(0,165)}`}if(e.kind==='tool.started')return `Agent ${e.payload.agent} invoking ${e.payload.tool}`;if(e.kind==='plan.generated')return `Mode: ${e.payload.mode}; tools: ${(e.payload.tasks||[]).join(', ')}`;if(e.kind==='verification.completed')return `Verdict: ${e.payload.verdict}; checks: ${JSON.stringify(e.payload.counts)}`;if(e.kind==='mission.created')return `Execution mode: ${e.payload.mode}`;if(e.kind==='report.generated')return `Artifact written: ${e.payload.artifact}`;return JSON.stringify(e.payload).slice(0,180)}
function privateToken(){if(!app.missionToken){const input=window.prompt('Enter private WORLDTRACE mission token (not an AI provider key). Stored in tab memory only.');if(!input)return null;app.missionToken=input.trim()}return app.missionToken}
async function submitRecoveryReview(id,tool,decision){const token=privateToken();if(!token)return;const reviewer=window.prompt('Reviewer name (recorded in audit log):');if(!reviewer||reviewer.trim().length<2)return;const note=window.prompt('Optional review note (do not enter private data):')||'';try{await api('/api/missions/'+encodeURIComponent(id)+'/reviews',{method:'POST',headers:{'Content-Type':'application/json','X-WORLDTRACE-TOKEN':token},body:JSON.stringify({tool,decision,reviewer:reviewer.trim(),note:note.slice(0,500)})});await showMission(id);renderSelectedReview()}catch(e){if(/403|authorization/i.test(e.message))app.missionToken=null;$('error').hidden=false;$('error').textContent='Review not saved: '+e.message}}
function reviewPanel(mission){if(mission.status!=='completed')return '';const proposed=mission.events.find(e=>e.kind==='recovery.proposed');if(!proposed)return '';const reviewed=new Set(mission.events.filter(e=>e.kind==='recovery.reviewed').map(e=>e.payload.tool));const pending=(proposed.payload.proposals||[]).filter(p=>!reviewed.has(p.tool));if(!pending.length)return '<div class="stream-entry"><strong>HUMAN REVIEW</strong><div class="entry-detail">All proposed actions have recorded dispositions. No repairs were executed.</div></div>';return '<div class="stream-entry"><strong>HUMAN REVIEW · MANUAL FOLLOW-UP ONLY</strong><div class="entry-detail">Approval records a decision; it does NOT execute an action.</div>'+pending.map(p=>'<div class="entry-detail" style="margin-top:12px"><strong>'+safe(p.tool)+'</strong>: '+safe(p.proposed_action)+'<div style="margin-top:7px"><button class="tiny-btn" data-review-tool="'+safe(p.tool)+'" data-review-decision="approve_for_manual_followup">Approve manual follow-up</button> <button class="tiny-btn" data-review-tool="'+safe(p.tool)+'" data-review-decision="reject">Reject</button></div></div>').join('')+'</div>'}
async function showMission(id){app.active=id;try{const d=await api(`/api/missions/${encodeURIComponent(id)}`);$('metricAudit').textContent=d.audit_chain_valid?'VALID':'FAILED';$('streamStatus').textContent=`${d.id} / ${d.status.toUpperCase()} / ${d.mode.toUpperCase()}`;$('streamCount').textContent=`${d.events.length} EVENTS`;$('stream').innerHTML=d.events.map(e=>{const status=e.payload?.status==='passed'?'pass':e.payload?.status==='finding'?'finding':e.kind==='tool.failed'?'error':'';return `<div class="stream-entry ${status}"><div class="entry-top"><span class="entry-name">${safe(e.kind.replaceAll('.',' / ').toUpperCase())}</span><span class="entry-time">${safe(e.time.slice(11,19))} UTC</span></div><div class="entry-detail">${safe(describeEvent(e))}</div></div>`}).join('')+reviewPanel(d);$('stream').querySelectorAll('[data-review-tool]').forEach(button=>button.onclick=()=>submitRecoveryReview(d.id,button.dataset.reviewTool,button.dataset.reviewDecision));if(!d.events.some(e=>e.kind==='recovery.proposed'))$('stream').scrollTop=$('stream').scrollHeight;
if(d.status==='completed'||d.status==='error'){clearInterval(app.timer);app.timer=null;const button=$('run');button.disabled=false;button.innerHTML='<span>✳</span> Execute mission <span>→</span>';await refresh()}
return d}catch(e){$('error').hidden=false;$('error').textContent=e.message}}
$('run').onclick=async()=>{$('error').hidden=true;const goal=$('goal').value.trim();if(goal.length<12){$('error').hidden=false;$('error').textContent='Please provide a mission with at least 12 characters.';return}const button=$('run');button.disabled=true;button.textContent='Starting mission…';try{let headers={'Content-Type':'application/json'};if(app.mode==='model'){const token=privateToken();if(!token)throw Error('Model mission cancelled: a private WORLDTRACE mission token is required.');headers['X-WORLDTRACE-TOKEN']=token}const d=await api('/api/missions',{method:'POST',headers,body:JSON.stringify({goal,mode:app.mode})});button.textContent='Mission in progress…';await refresh();await showMission(d.id);if(app.timer)clearInterval(app.timer);if(!['completed','error'].includes((await api('/api/missions/'+encodeURIComponent(d.id))).status))app.timer=setInterval(()=>showMission(d.id),950)}catch(e){if(app.mode==='model'&&/authorization|403|token/i.test(e.message))app.missionToken=null;button.disabled=false;button.innerHTML='<span>✳</span> Execute mission <span>→</span>';$('error').hidden=false;$('error').textContent=e.message}}
async function launchTool(tool){app.workspaceTool=tool;app.workspaceSource=document.getElementById('agents').classList.contains('shown')?'agents':'tools';route('workspace');$('workspaceResult').innerHTML='<div class="module-result-placeholder">Run this fixture tool to generate a recorded finding.</div>';$('workspaceError').hidden=true;const run=$('runOneTool');run.disabled=false;run.textContent='▶ Run this tool on its approved fixture →';try{const info=await api('/api/tools/'+encodeURIComponent(tool)+'/workspace');configureUpload(tool);$('workspaceTitle').textContent=info.title;$('workspaceRole').textContent=info.role;$('workspacePurpose').textContent=info.purpose;$('workspaceFixture').textContent=info.fixture;$('workspaceSteps').innerHTML=info.steps.map((step,i)=>'<li><span class="step-number">'+String(i+1).padStart(2,'0')+'</span><span>'+safe(step)+'</span></li>').join('');$('workspaceLimitation').textContent='SCOPE BOUNDARY: '+info.limitation;await loadToolHistory()}catch(e){$('workspaceError').hidden=false;$('workspaceError').textContent='Workspace unavailable: '+e.message}}
async function loadToolHistory(){if(!app.workspaceTool)return;try{const runs=await api('/api/tools/'+encodeURIComponent(app.workspaceTool)+'/runs');$('workspaceHistory').innerHTML=runs.length?runs.map(run=>'<button type="button" class="workspace-run-record" data-run-id="'+safe(run.id)+'"><span><strong>'+safe(run.id)+'</strong><small>'+safe(run.completed)+'</small></span><span class="run-status '+safe(run.status)+'">'+safe(run.status.toUpperCase())+'</span></button>').join(''):'<div class="review-empty">No previous runs for this module.</div>';$('workspaceHistory').querySelectorAll('[data-run-id]').forEach(button=>button.onclick=()=>loadRecordedRun(button.dataset.runId))}catch(e){$('workspaceHistory').textContent='History unavailable: '+e.message}}
function resultExplanation(tool,result,source){
 const uploaded=source==='upload';
 if(tool==='pdf_inspect'){
   if(uploaded){return result.characters>0
     ?'PDF successfully processed: '+result.pages+' page(s), '+result.characters+' text characters extracted. Signature and tax-ID words are informational only; they are NOT required for a general document.'
     :'PDF file opened, but readable text was not extracted. For scanned PDFs, OCR is required (not yet available).';}
   return result.checks?.signed===false
     ?'The sample supplier PDF was read. Its signature check failed, so it needs manual review. This does NOT mean your uploaded PDF failed.'
     :'Sample supplier PDF checks completed. Review the detailed checks below.';
 }
 if(tool==='etl_compare')return result.pass?'Both CSV datasets match on their record IDs and values.':'Data differences were detected. Check missing, extra and mismatched IDs in the evidence below.';
 if(tool==='email_inspect')return result.pass?'Email fields passed the checks. No mail was sent.':'One or more email checks need review. No mail was sent.';
 if(tool==='network_inspect')return result.failure_count?'The HAR log contains '+result.failure_count+' failed HTTP request(s). No live traffic was captured.':'No HTTP errors were identified in the analyzed HAR.';
 if(tool==='api_virtualize')return result.pass?'Expected and simulated HTTP statuses match. No external API was called.':'Expected and simulated HTTP statuses differ. This is a local contract check.';
 if(tool==='middleware_test')return result.duplicates?.length?'Duplicate message IDs were identified in the provided data.':'No duplicate message IDs were found in the analyzed data.';
 if(tool==='mainframe_contract')return result.invalid_lines?.length?'Some fixed-width records have invalid length or prefixes.':'The fixed-width records passed the configured checks.';
 if(tool==='database_check')return result.pending?'The synthetic database has '+result.pending+' pending record(s).':'No pending suppliers were found in the synthetic database.';
 if(tool==='performance_probe')return 'In-process hashing workload was timed; this is NOT a production load test.';
 return 'Local checks completed. Review the recorded evidence and scope.';
}
function explainChecks(result){
 const checks=result.checks||{};
 const entries=Object.entries(checks);
 if(!entries.length)return '';
 return '<div class="human-checks">'+entries.map(([key,value])=>{
  const info=key==='mentions_signature'?'Signature-related words found (not signature authenticity)':key==='mentions_tax_id'?'Tax-ID-related words found (not mandatory)':key==='has_text'?'Readable text extracted':key==='signed'?'Sample signature assertion':key.replaceAll('_',' ');
  return '<div class="human-check"><span>'+safe(info)+'</span><strong>'+ (value?'YES':'NO')+'</strong></div>';
 }).join('')+'</div>';
}
function evidenceCard(tool,result,source,status,runId){
 const label=status==='passed'?'CHECKS PASSED':status==='finding'?'REVIEW NEEDED':'EXECUTION ERROR';
 const color=status==='passed'?'passed':status==='finding'?'finding':'error';
 return '<div class="human-result"><div class="human-result-head"><strong>What happened?</strong><span class="run-status '+safe(color)+'" title="Result status; not a button">'+label+'</span></div><p>'+safe(resultExplanation(tool,result,source))+'</p><div class="human-result-note">'+(source==='upload'?'Source: your selected uploaded file · No permanent raw upload storage':'Source: WORLDTRACE synthetic test fixture · Recorded in run history')+(runId?' · Run '+safe(runId):'')+'</div></div>'+explainChecks(result);
}
function displayRecordedRun(run){const result=run.result||{};const badges=Object.entries(result).filter(([key,value])=>['pass','file','pages','rows','pending','failure_count','missing_ids','duplicates','records','p95_ms','expected','simulated'].includes(key)).map(([key,value])=>'<div class="result-fact"><span>'+safe(key.replaceAll('_',' '))+'</span><b>'+safe(Array.isArray(value)?value.join(', ')||'none':value)+'</b></div>').join('');$('workspaceResult').innerHTML=evidenceCard(run.tool,result,'fixture',run.status,run.id)+'<div class="result-heading"><span class="result-label">DETAILED EVIDENCE</span><strong>'+safe(run.id)+'</strong></div><div class="result-facts">'+badges+'</div><div class="eyebrow">RECORDED BACKEND EVIDENCE</div><pre class="result-json">'+safe(JSON.stringify(result,null,2))+'</pre><div class="result-footer">Source: synthetic local fixture · '+safe(run.completed)+' · No external writes or production access</div>'}
async function loadRecordedRun(runId){try{const run=await api('/api/tool-runs/'+encodeURIComponent(runId));if(run.tool!==app.workspaceTool)throw Error('Run does not belong to selected tool');displayRecordedRun(run)}catch(e){$('workspaceError').hidden=false;$('workspaceError').textContent=e.message}}
$('runOneTool').onclick=async()=>{if(!app.workspaceTool)return;const button=$('runOneTool');button.disabled=true;button.textContent='Executing approved fixture…';$('workspaceError').hidden=true;try{const run=await api('/api/tools/'+encodeURIComponent(app.workspaceTool)+'/runs',{method:'POST'});displayRecordedRun(run);await loadToolHistory()}catch(e){$('workspaceError').hidden=false;$('workspaceError').textContent='Execution failed: '+e.message}finally{button.disabled=false;button.textContent='▶ Run this tool on its approved fixture →'}};
$('workspaceBack').onclick=()=>route(app.workspaceSource);
$('workspaceRefresh').onclick=loadToolHistory;
function renderReviewQueue(){const select=$('reviewMissionSelect');const previous=select.value;const completed=app.missions.filter(m=>m.status==='completed');select.innerHTML='<option value="">Select a completed mission</option>'+completed.map(m=>'<option value="'+safe(m.id)+'">'+safe(m.id)+' · '+safe(m.goal.slice(0,72))+'</option>').join('');if(completed.some(m=>m.id===previous))select.value=previous;else if(completed.length)select.value=completed[0].id;renderSelectedReview()}
async function renderSelectedReview(){const id=$('reviewMissionSelect').value;if(!id){$('reviewQueue').innerHTML='<div class="review-empty">No completed missions yet. Launch a synthetic workflow in Mission Control first.</div>';return}try{const mission=await api('/api/missions/'+encodeURIComponent(id));const proposed=mission.events.find(e=>e.kind==='recovery.proposed');const proposals=proposed?.payload?.proposals||[];const reviewed=new Map(mission.events.filter(e=>e.kind==='recovery.reviewed').map(e=>[e.payload.tool,e.payload]));$('reviewQueue').innerHTML='<div class="review-summary"><span>MISSION '+safe(mission.id)+'</span><strong>'+proposals.length+' ACTIONS PROPOSED · '+reviewed.size+' REVIEWED</strong></div>'+(proposals.length?proposals.map(p=>{const decision=reviewed.get(p.tool);return '<article class="review-item"><div><span class="review-tool">'+safe(p.tool)+'</span><h3>'+safe(p.proposed_action)+'</h3><p>Suggested owner: '+safe(p.owner)+' · Fixture finding only</p></div><div class="review-decision">'+(decision?'<span class="review-done">✓ '+safe(decision.decision.replaceAll('_',' '))+' — '+safe(decision.reviewer)+'</span>':'<button type="button" class="tiny-btn" data-review-tool="'+safe(p.tool)+'" data-review-decision="approve_for_manual_followup">Approve manual follow-up</button><button type="button" class="tiny-btn reject-btn" data-review-tool="'+safe(p.tool)+'" data-review-decision="reject">Reject</button>')+'</div></article>'}).join(''):'<div class="review-empty">No recovery proposals for this mission. No action needed.</div>');$('reviewQueue').querySelectorAll('[data-review-tool]').forEach(b=>b.onclick=()=>submitRecoveryReview(id,b.dataset.reviewTool,b.dataset.reviewDecision))}catch(e){$('reviewQueue').textContent='Review queue unavailable: '+e.message}}
$('reviewMissionSelect').onchange=renderSelectedReview;
async function showAudit(id){try{const d=await api('/api/missions/'+encodeURIComponent(id));$('auditBody').innerHTML='<div class="ledger-verify '+(d.audit_chain_valid?'':'bad')+'">'+(d.audit_chain_valid?'✓ VERIFIED HASH CHAIN':'✗ AUDIT INTEGRITY ERROR')+' · '+d.events.length+' stored events</div>'+d.events.map(e=>'<div class="ledger-row"><div><div class="ledger-kind">'+safe(e.kind)+'</div><div class="muted">'+safe(e.time.replace('T',' ').slice(0,19))+' UTC</div></div><div class="ledger-payload">'+safe(JSON.stringify(e.payload))+'<div class="muted" style="margin-top:5px">SHA-256 '+safe(e.event_hash)+'</div></div></div>').join('')}catch(e){$('auditBody').textContent=e.message}}
$('auditMission').onchange=e=>{if(!e.target.value){$('auditBody').textContent='Select a mission to inspect evidence.';return}showAudit(e.target.value)};

(async()=>{try{await refresh();renderCapabilities(await api('/api/capabilities'));$('connection').textContent='● LOCAL ENGINE'}catch(e){$('connection').textContent='● OFFLINE'}})();

async function downloadPrivatePackage(url,id,token){
  const response=await fetch(url,{headers:{'X-WORLDTRACE-TOKEN':token}});
  if(!response.ok)throw Error('Download failed: HTTP '+response.status);
  const blob=await response.blob();
  const objectUrl=URL.createObjectURL(blob);
  try{
    const anchor=document.createElement('a');
    anchor.href=objectUrl;anchor.download=id+'.zip';
    document.body.appendChild(anchor);anchor.click();anchor.remove();
  }finally{setTimeout(()=>URL.revokeObjectURL(objectUrl),2500)}
}
$('buildDeliverable').onclick=async()=>{
 const token=privateToken();if(!token)return;
 const button=$('buildDeliverable'),error=$('outcomeError');
 error.hidden=true;button.disabled=true;button.textContent='Generating actual files…';
 try{
  const request={domain:$('outcomeDomain').value,goal:$('outcomeGoal').value.trim(),evidence:$('outcomeEvidence').value};
  const data=await api('/api/deliverables',{method:'POST',headers:{'Content-Type':'application/json','X-WORLDTRACE-TOKEN':token},body:JSON.stringify(request)});
  $('outcomeTrace').innerHTML=data.events.map(e=>'<div class="outcome-stage"><span class="step-number">'+String(e.sequence).padStart(2,'0')+'</span><div><b>'+safe(e.agent)+'</b><p>'+safe(e.operation.replaceAll('_',' '))+'</p></div><span class="stage-check">✓</span></div>').join('');
  $('outcomeDelivery').innerHTML='<div class="delivery-done"><strong>✓ VERIFIED PACKAGE CREATED</strong><p>'+safe(data.id)+' · '+data.files.length+' recorded files · No external changes.</p><button class="primary-btn" id="downloadOutcome">↓ Download actual ZIP deliverable</button></div>';
  $('downloadOutcome').onclick=async()=>{try{await downloadPrivatePackage(data.download_url,data.id,token)}catch(e){error.hidden=false;error.textContent=e.message}};
 }catch(e){if(/authorization|403|token/i.test(e.message))app.missionToken=null;error.hidden=false;error.textContent=e.message}
 finally{button.disabled=false;button.textContent='✦ Produce verified delivery package →'}
};

const UPLOAD_TYPES={
 pdf_inspect:'.pdf',email_inspect:'.eml',network_inspect:'.har',
 etl_compare:'.csv',api_virtualize:'.json',middleware_test:'.json',mainframe_contract:'.txt'
};
function configureUpload(tool){
 const supported=Object.hasOwn(UPLOAD_TYPES,tool);
 $('uploadPanel').hidden=!supported;
 $('uploadMain').value='';$('uploadComparison').value='';
 $('uploadError').hidden=true;
 if(!supported)return;
 $('uploadMain').accept=UPLOAD_TYPES[tool];
 $('uploadComparisonBox').hidden=tool!=='etl_compare';
}
function displayUploadedResult(data){
 const result=data.result||{};
 $('workspaceResult').innerHTML=evidenceCard(data.tool,result,'upload',data.status,null)+'<div class="result-heading"><span class="result-label">YOUR FILE — DETAILED EVIDENCE</span><strong>FILE ANALYSIS</strong></div>'+
 '<div class="result-facts"><div class="result-fact"><span>FILE</span><b>'+safe(data.file_name)+'</b></div><div class="result-fact"><span>SHA-256</span><b>'+safe(data.sha256)+'</b></div></div>'+
 '<div class="eyebrow">REAL FILE PARSER OUTPUT (NOT AI)</div><pre class="result-json">'+safe(JSON.stringify(result,null,2))+'</pre>'+
 '<div class="result-footer">This result came from the selected file. The upload is analyzed in memory, is not stored as a tool run, and is not externally verified.</div>';
}
$('analyzeUpload').onclick=async()=>{
 const tool=app.workspaceTool;
 if(!Object.hasOwn(UPLOAD_TYPES,tool))return;
 const error=$('uploadError');error.hidden=true;
 const file=$('uploadMain').files?.[0];
 const target=$('uploadComparison').files?.[0];
 if(!file || (tool==='etl_compare'&&!target)){error.hidden=false;error.textContent=tool==='etl_compare'?'Select both source and target CSV files.':'Select a file to analyze.';return;}
 if(file.size>2097152 || (target&&target.size>2097152)){error.hidden=false;error.textContent='Each uploaded file must be at most 2 MiB.';return;}
 const token=privateToken();if(!token)return;
 const button=$('analyzeUpload');button.disabled=true;button.textContent='Analyzing actual file…';
 try{
   const form=new FormData();form.append('file',file);
   if(target)form.append('comparison',target);
   const response=await fetch('/api/tools/'+encodeURIComponent(tool)+'/inspect-upload',{method:'POST',headers:{'X-WORLDTRACE-TOKEN':token},body:form});
   const data=await response.json().catch(()=>({detail:'Invalid server response'}));
   if(!response.ok)throw Error(data.detail||('HTTP '+response.status));
   if(app.workspaceTool===tool)displayUploadedResult(data);
 }catch(e){if(/403|authorization|token/i.test(e.message))app.missionToken=null;error.hidden=false;error.textContent='Upload analysis failed: '+e.message}
 finally{button.disabled=false;button.textContent='Analyze uploaded file →'}
};

function summarizeObservation(item){
 const r=item.result||{};
 if(item.tool==='etl_compare'){
  const missing=(r.missing_ids||[]),extra=(r.extra_ids||[]),mismatch=(r.mismatched_ids||[]);
  return 'Source '+r.source_rows+' rows · Target '+r.target_rows+' rows · Missing: '+(missing.join(', ')||'none')+' · Extra: '+(extra.join(', ')||'none')+' · Value mismatches: '+(mismatch.join(', ')||'none');
 }
 if(item.tool==='pdf_inspect')return r.pages+' pages · '+r.characters+' extracted characters. This is text extraction, not accuracy verification.';
 if(item.tool==='network_inspect')return r.failure_count+' HTTP failures among '+r.total_requests+' recorded requests.';
 if(item.tool==='email_inspect')return 'Sender '+(r.has_sender?'found':'missing')+' · Subject '+(r.has_subject?'found':'missing')+'. No message was sent.';
 if(item.tool==='api_virtualize')return 'Expected HTTP '+r.expected_status+' · Simulated HTTP '+r.simulated_status+'. No live API requested.';
 if(item.tool==='middleware_test')return (r.duplicates||[]).length+' duplicate message IDs detected.';
 if(item.tool==='mainframe_contract')return (r.invalid_lines||[]).length+' invalid fixed-width rows detected.';
 return item.status==='passed'?'Configured check passed.':'Review individual tool evidence.';
}
const multiFileFor=(role,id)=>app.guidedDemoFiles?.[role]||$(id).files?.[0];
$('loadGuidedDemo').onclick=()=>{
 app.guidedDemoFiles={
   source_csv:new File(['id,name\nA1,Alpha\nA2,Beta\nA3,Gamma\n'],'demo-source.csv',{type:'text/csv'}),
   target_csv:new File(['id,name\nA1,Alpha\nA2,Beta\n'],'demo-target.csv',{type:'text/csv'})
 };
 $('multiGoal').value='Investigate a missing supplier onboarding record. Propose a controlled repair, obtain human approval, execute on an isolated demo database, and prove the before/after result.';
 $('multiRetain').checked=true;
 $('multiModel').checked=false;
 $('guidedDemoStatus').textContent='SAFE DEMO LOADED · 3 source rows / 2 target rows. Next: Execute multi-file analysis, then approve in Human Review.';
 $('multiResults').innerHTML='<div class="review-empty">Demo inputs ready. Click Execute multi-file analysis to detect the missing record. The model checkbox stays off until Baseten access works.</div>';
};
const multiFields=[
 ['pdf','multiPdf'],['email','multiEmail'],['har','multiHar'],
 ['source_csv','multiSource'],['target_csv','multiTarget'],
 ['api_json','multiApi'],['messages_json','multiMessages'],['legacy_txt','multiLegacy']
];
$('multiRun').onclick=async()=>{
 const error=$('multiError');error.hidden=true;
 const goal=$('multiGoal').value.trim();
 const selected=multiFields.filter(([role,id])=>Boolean(multiFileFor(role,id)));
 if(goal.length<12){error.hidden=false;error.textContent='Enter an instruction of at least 12 characters.';return}
 if(!selected.length){error.hidden=false;error.textContent='Select one or more input files.';return}
 if(selected.some(([role,id])=>multiFileFor(role,id).size>2097152)){
  error.hidden=false;error.textContent='Each file must be 2 MiB or smaller.';return;
 }
 if(selected.some(([role])=>role==='source_csv') !== selected.some(([role])=>role==='target_csv')){
  error.hidden=false;error.textContent='For data comparison, select BOTH source and target CSV files.';return;
 }
 const token=privateToken();if(!token)return;
 const btn=$('multiRun');btn.disabled=true;btn.textContent='Executing actual file checks…';
 try{
   const body=new FormData();body.append('goal',goal);body.append('retain_result',$('multiRetain').checked?'true':'false');body.append('model_planning',$('multiModel').checked?'true':'false');
   for(const [role,id] of selected)body.append(role,multiFileFor(role,id));
   const res=await fetch('/api/multi-file-missions/run',{
    method:'POST',headers:{'X-WORLDTRACE-TOKEN':token},body});
   const data=await res.json().catch(()=>({detail:'Invalid server response'}));
   if(!res.ok)throw Error(data.detail||'HTTP '+res.status);
   const findings=data.observations.filter(o=>o.status!=='passed');
   const intro='<div class="human-result"><div class="human-result-head"><strong>Mission outcome</strong><span class="run-status '+(data.status==='LOCAL_CHECKS_PASSED'?'passed':'finding')+'">'+safe(data.status.replaceAll('_',' '))+'</span></div><p>'+data.observations.length+' actual file analyses complete · '+findings.length+' require review · '+data.cross_checks.length+' cross-file consistency checks.</p><div class="human-result-note">'+(data.model_plan?'Actual model-planned tool order · '+safe(data.model_plan.model)+' · ':'Deterministic local plan · ')+'Deterministic parsers and checks. No external changes. Storage only if explicitly selected.</div></div>';
   const planNote=data.model_plan?'<div class="human-result"><strong>Meta model plan verified by provider response</strong><p>'+safe(data.model_plan.reason)+'</p><small>Provider model: '+safe(data.model_plan.model)+' · Ordered file roles: '+safe(data.model_plan.ordered_roles.join(', '))+'</small></div>':'';
   const modelReasoning=data.model_assessment?'<div class="human-result"><strong>REAL MODEL EVIDENCE ASSESSMENT (ADVISORY)</strong><p>'+safe(data.model_assessment.summary)+'</p>'+data.model_assessment.hypotheses.map(h=>'<p>Hypothesis: '+safe(h.claim)+' · '+safe(h.confidence)+' confidence · Sources: '+safe(h.evidence_roles.join(', '))+'</p>').join('')+'<p><strong>Next:</strong> '+safe(data.model_assessment.next_action)+'</p></div>':'';
   const records=data.observations.map(o=>'<div class="outcome-stage"><span class="run-status '+safe(o.status)+'">'+safe(o.status.toUpperCase())+'</span><div><b>'+safe(o.file_name)+'</b><p>'+safe(summarizeObservation(o))+'</p><small>'+safe(o.tool)+' · SHA-256 '+safe(o.sha256.slice(0,16))+'…</small></div></div>').join('');
   const correlations=data.cross_checks.map(c=>'<div class="outcome-stage"><strong>'+safe(c.matched?'MATCH':'MISMATCH')+'</strong><div><b>'+safe(c.name)+'</b><p>'+safe(c.basis)+'</p></div></div>').join('');
   const mission={id:data.saved_mission_id||'SESSION-'+String(Date.now()),goal,created:new Date().toISOString(),data};
   app.unifiedMissions.unshift(mission);app.unifiedMissions=app.unifiedMissions.slice(0,5);app.selectedUnified=mission.id;
   renderAgentWorkforce();
   if(data.saved_mission_id)await loadUnifiedHistory(token);
   $('multiResults').innerHTML=intro+planNote+modelReasoning+'<div class="eyebrow">INDIVIDUAL FILE RESULTS</div>'+records+'<div class="eyebrow multi-spaced">CROSS-FILE CHECKS</div>'+(correlations||'<p class="muted">No matching cross-file check for selected types.</p>')+'<div class="eyebrow multi-spaced">EXECUTION TRACE</div>'+data.trace.map(e=>'<div class="outcome-stage"><span class="step-number">'+safe(e.role.split(' ')[0])+'</span><div><b>'+safe(e.role)+'</b><p>'+safe(e.action.replaceAll('_',' '))+'</p></div></div>').join('')+'<div class="multi-actions"><button type="button" class="run-btn secondary-run" id="downloadMulti">↓ Download verified Markdown report</button><button type="button" class="tiny-btn" id="inspectMissionAgents">◉ Inspect Agent Workforce →</button><button type="button" class="tiny-btn" id="prepareOutcome">✦ Prepare final delivery package →</button>'+(data.saved_mission_id?'<button type="button" class="run-btn secondary-run" id="reviewMissionNow">✓ Review and resolve in demo →</button>':'')+'</div>';
   $('inspectMissionAgents').onclick=()=>route('agents');
   $('prepareOutcome').onclick=()=>importLatestUnifiedEvidence();
   if(data.saved_mission_id)$('reviewMissionNow').onclick=()=>{route('reviews');loadUnifiedReviewQueue(token,data.saved_mission_id)};
   $('downloadMulti').onclick=()=>{
     const blob=new Blob([data.report_markdown],{type:'text/markdown;charset=utf-8'});
     const url=URL.createObjectURL(blob);
     const a=document.createElement('a');a.href=url;a.download='WORLDTRACE-multifile-report.md';document.body.appendChild(a);a.click();a.remove();
     setTimeout(()=>URL.revokeObjectURL(url),3000);
   };
 }catch(e){error.hidden=false;error.textContent='Mission failed: '+e.message}
 finally{btn.disabled=false;btn.textContent='▶ Execute multi-file analysis →'}
};

const RESPONSIBILITIES=[
 ['Research Agent','Inventory and identify supplied evidence','inventory_user_evidence'],
 ['Security Agent','Enforce bounded file and execution policy','enforce_bounded_parsers'],
 ['Execution Agent','Execute approved file parsers','inspect_real_file'],
 ['Verification Agent','Check findings and cross-file consistency','compare_evidence_and_checks'],
 ['Builder Agent','Prepare evidence-backed human follow-up','prepare_review_actions'],
 ['Delivery Agent','Generate verified final report','produce_verified_markdown']
];
function renderAgentWorkforce(){
 const sel=$('agentMissionSelect');
 const previous=sel.value || app.selectedUnified;
 sel.innerHTML='<option value="">Select a unified mission from this browser session</option>'+
 app.unifiedMissions.map(m=>'<option value="'+safe(m.id)+'">'+safe(m.goal.slice(0,70))+' · '+safe(m.created.slice(11,19))+'</option>').join('');
 if(app.unifiedMissions.some(m=>m.id===previous))sel.value=previous;
 const mission=app.unifiedMissions.find(m=>m.id===sel.value);
 $('agentMissionSummary').innerHTML=mission?
 '<strong>'+safe(mission.goal)+'</strong><p>'+mission.data.observations.length+' analyzed file roles · '+mission.data.proposed_actions.length+' manual follow-ups · '+safe(mission.data.status.replaceAll('_',' '))+'</p><button type="button" class="tiny-btn" id="agentToMission">Review mission outcome</button>':
 'No mission selected. To try all six responsibility views, click “Run public supplier demo — no key needed” above, then start the demo. You can also load private UM- missions with your operator token.';
 if(mission)$('agentToMission').onclick=()=>{route('multi');$('multiResults').scrollIntoView({behavior:'smooth'})};
 $('agentGrid').innerHTML=RESPONSIBILITIES.map(([title,description,event])=>{
  const matched=mission?mission.data.trace.filter(e=>e.action===event):[];
  const count=matched.length;
  const outcome=mission?count+' recorded operation'+(count===1?'':'s'):'Awaiting mission';
  return '<article class="agent-card role-card"><div class="agent-icon">◈</div><h3>'+safe(title)+'</h3><p>'+safe(description)+'</p><div class="mini-status">'+safe(outcome)+'</div>'+
    (mission?'<div class="role-evidence">'+matched.map(e=>'<div><strong>'+safe(e.action.replaceAll('_',' '))+'</strong><small>'+safe(JSON.stringify(e.details).slice(0,260))+'</small></div>').join('')+'</div>':'')+
   '<button type="button" class="tiny-btn agent-evidence-btn" data-role-detail="'+safe(title)+'">Inspect role and evidence →</button></article>'
 }).join('');
 $('agentGrid').querySelectorAll('[data-role-detail]').forEach(btn=>btn.onclick=()=>{
   const title=btn.dataset.roleDetail;
   const responsibility=RESPONSIBILITIES.find(x=>x[0]===title);
   const matching=mission?mission.data.trace.filter(e=>e.role===title):[];
   $('agentRoleDetail').innerHTML='<h2>'+safe(title)+'</h2><p>'+safe(responsibility?.[1]||'Scoped responsibility')+'</p>'+
    (mission?'<p><strong>Mission:</strong> '+safe(mission.id)+' · '+matching.length+' actual stage records</p>'+
      matching.map(e=>'<div class="role-evidence-detail"><strong>'+safe(e.action.replaceAll('_',' '))+'</strong><p>'+safe(JSON.stringify(e.details,null,2))+'</p><small>Event SHA-256: '+safe(e.hash)+'</small></div>').join(''):
      '<p>No mission evidence yet. Start the guided supplier-resolution demo from Mission Control, then return to inspect actual operations.</p>');
   $('agentRoleDetail').scrollIntoView({behavior:'smooth',block:'nearest'});
 });
}
$('agentMissionSelect').onchange=e=>{app.selectedUnified=e.target.value;renderAgentWorkforce()};
$('agentStartDemo').onclick=()=>{
 route('multi');
 $('startPublicDemo').scrollIntoView({behavior:'smooth',block:'center'});
};

async function loadUnifiedHistory(providedToken){
 const err=$('multiError');
 const token=providedToken||privateToken();if(!token)return;
 try{
   const items=await api('/api/unified-missions',{headers:{'X-WORLDTRACE-TOKEN':token}});
   $('unifiedHistory').innerHTML=items.length?
      items.map(m=>'<button type="button" class="workspace-run-record" data-unified-id="'+safe(m.id)+'"><span><strong>'+safe(m.id)+'</strong><small>'+safe(m.goal.slice(0,95))+'</small></span><span>'+safe(m.status.replaceAll('_',' '))+'</span></button>').join(''):
      '<div class="review-empty">No saved unified missions yet. Select the save checkbox before execution.</div>';
   $('unifiedHistory').querySelectorAll('[data-unified-id]').forEach(btn=>btn.onclick=()=>openUnifiedMission(btn.dataset.unifiedId,token));
 }catch(e){if(/403|authorization|token/i.test(e.message))app.missionToken=null;err.hidden=false;err.textContent='Could not load saved missions: '+e.message}
}
async function openUnifiedMission(id,token){
 const err=$('multiError');err.hidden=true;
 try{
   const data=await api('/api/unified-missions/'+encodeURIComponent(id),{headers:{'X-WORLDTRACE-TOKEN':token}});
   const existing=app.unifiedMissions.find(m=>m.id===id);
   if(!existing)app.unifiedMissions.unshift({id,goal:data.goal,created:data.created,data});
   else existing.data=data;
   app.selectedUnified=id;
   renderAgentWorkforce();
   const names=data.observations.map(o=>'<div class="outcome-stage"><span class="run-status '+safe(o.status)+'">'+safe(o.status.toUpperCase())+'</span><div><b>'+safe(o.file_name)+'</b><p>'+safe(o.tool)+'</p></div></div>').join('');
   $('multiResults').innerHTML='<div class="human-result"><strong>Saved mission '+safe(id)+'</strong><p>'+safe(data.goal)+'</p><p>'+safe(data.status.replaceAll('_',' '))+' · '+data.observations.length+' processed roles · '+data.proposed_actions.length+' follow-up proposals</p></div>'+names+
    '<div class="multi-actions"><button class="run-btn secondary-run" id="downloadSavedUnified">↓ Download saved report</button><button class="tiny-btn" id="viewSavedAgents">◉ View agent responsibilities</button><button class="tiny-btn" id="reviewSavedActions">✓ Review actions</button></div>';
   $('downloadSavedUnified').onclick=()=>downloadMarkdown(data.report_markdown,id+'.md');
   $('viewSavedAgents').onclick=()=>route('agents');
   $('reviewSavedActions').onclick=()=>{route('reviews');loadUnifiedReviewQueue(token,id)};
   route('multi');
 }catch(e){if(/403|authorization|token/i.test(e.message))app.missionToken=null;err.hidden=false;err.textContent='Could not open saved mission: '+e.message}
}
function downloadMarkdown(report,filename){
 const url=URL.createObjectURL(new Blob([report],{type:'text/markdown;charset=utf-8'}));
 const a=document.createElement('a');a.href=url;a.download=filename;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),3000);
}
$('loadUnifiedHistory').onclick=()=>loadUnifiedHistory();
async function loadUnifiedReviewQueue(providedToken,selectedId){
 const token=providedToken||privateToken();if(!token)return;
 const out=$('unifiedReviewQueue');
 try{
  const rows=await api('/api/unified-missions',{headers:{'X-WORLDTRACE-TOKEN':token}});
  const records=await Promise.all(rows.slice(0,20).map(r=>api('/api/unified-missions/'+encodeURIComponent(r.id),{headers:{'X-WORLDTRACE-TOKEN':token}})));
  const selected=selectedId?records.filter(r=>r.id===selectedId):records;
  out.innerHTML=selected.map(r=>{
   const decisions=new Map((r.decisions||[]).map(d=>[d.action_index,d.decision]));
   const executed=new Map((r.sandbox_executions||[]).map(x=>[x.action_index,x]));
   return '<div class="unified-review-record"><strong>'+safe(r.id)+' · '+safe(r.goal.slice(0,85))+'</strong>'+
    (r.proposed_actions.length?r.proposed_actions.map((a,i)=>{
      const d=decisions.get(i), run=executed.get(i);
      const buttons=!d?'<button class="tiny-btn" data-unified-review="'+safe(r.id)+'" data-action-index="'+i+'" data-decision="approve_manual_followup">Approve manual follow-up</button> <button class="tiny-btn" data-unified-review="'+safe(r.id)+'" data-action-index="'+i+'" data-decision="reject">Reject</button>':
        run?'<div class="sandbox-verified"><strong>VERIFIED IN ISOLATED DEMO</strong><p>Before '+run.before_count+' → After '+run.after_count+' · '+run.added_records+' hashed records added. Original CSV untouched. No external changes.</p><small>Post-execution SHA-256 '+safe(run.after_digest)+'</small><button type="button" class="tiny-btn" data-receipt-id="'+safe(r.id)+'">↓ Download verified demo resolution receipt</button></div>':
        d==='approve_manual_followup'&&a.type==='sandbox_csv_reconcile'?
        '<button type="button" class="run-btn secondary-run" data-execute-demo="'+safe(r.id)+'" data-action-index="'+i+'">Execute approved demo correction & re-verify →</button>':
        '<small>'+safe(d.replaceAll('_',' '))+' recorded · No automatic external action.</small>';
      return '<div class="unified-review-action"><p><b>'+safe(a.type==='sandbox_csv_reconcile'?'CONTROLLED DEMO CORRECTION':'MANUAL REVIEW')+'</b> · '+safe(a.file||'Input')+': '+safe(a.next_action)+'</p>'+buttons+'</div>';
    }).join(''):'<p>No follow-up actions proposed.</p>')+'</div>';
  }).join('')||'<p>No saved missions found.</p>';
  out.querySelectorAll('[data-receipt-id]').forEach(btn=>btn.onclick=async()=>{
    try{
      const id=btn.dataset.receiptId;
      const data=await api('/api/unified-missions/'+encodeURIComponent(id),{
        headers:{'X-WORLDTRACE-TOKEN':token}});
      if(!data.resolution_report_markdown||!data.resolution_report_sha256)throw Error('Receipt not ready');
      downloadMarkdown(data.resolution_report_markdown,id+'-sandbox-resolution.md');
    }catch(e){out.insertAdjacentHTML('afterbegin','<p class="error">Receipt unavailable: '+safe(e.message)+'</p>')}
  });
  out.querySelectorAll('[data-execute-demo]').forEach(btn=>btn.onclick=async()=>{
    const confirmText='Execute only the APPROVED correction on an isolated SQLite demo copy of hashed CSV rows? Uploaded CSVs, external systems and production data remain unchanged.';
    if(!window.confirm(confirmText))return;
    btn.disabled=true;btn.textContent='Executing & verifying demo database…';
    try{
      const result=await api('/api/unified-missions/'+encodeURIComponent(btn.dataset.executeDemo)+'/execute-demo-correction',{
        method:'POST',headers:{'Content-Type':'application/json','X-WORLDTRACE-TOKEN':token},
        body:JSON.stringify({action_index:Number(btn.dataset.actionIndex)})});
      await loadUnifiedReviewQueue(token,selectedId);
      $('unifiedReviewQueue').insertAdjacentHTML('afterbegin','<div class="sandbox-verified"><strong>ACTUAL SANDBOX EXECUTION VERIFIED</strong><p>Added '+safe(result.rows_added)+' hashed records to local demo database. Before '+safe(result.before_count)+' → After '+safe(result.after_count)+'. Original source data unchanged.</p></div>');
    }catch(e){btn.disabled=false;btn.textContent='Retry demo correction';out.insertAdjacentHTML('afterbegin','<p class="error">Sandbox correction failed: '+safe(e.message)+'</p>')}
  });
  out.querySelectorAll('[data-unified-review]').forEach(btn=>btn.onclick=async()=>{
    const reviewer=window.prompt('Reviewer name for audit record:');
    if(!reviewer||reviewer.trim().length<2)return;
    const note=window.prompt('Optional review note (no confidential data):')||'';
    try{
     await api('/api/unified-missions/'+encodeURIComponent(btn.dataset.unifiedReview)+'/decisions',
       {method:'POST',headers:{'Content-Type':'application/json','X-WORLDTRACE-TOKEN':token},
        body:JSON.stringify({action_index:Number(btn.dataset.actionIndex),decision:btn.dataset.decision,reviewer:reviewer.trim(),note:note.slice(0,500)})});
     await loadUnifiedReviewQueue(token,selectedId);
    }catch(e){out.insertAdjacentHTML('afterbegin','<p class="error">Review failed: '+safe(e.message)+'</p>')}
  });
 }catch(e){if(/403|authorization|token/i.test(e.message))app.missionToken=null;out.textContent='Could not load reviews: '+e.message}
}
$('loadUnifiedReviews').onclick=()=>loadUnifiedReviewQueue();

$('probeModel').onclick=async()=>{
 const token=privateToken();if(!token)return;
 const btn=$('probeModel'),out=$('probeModelResult');
 btn.disabled=true;out.textContent='Sending one short real inference request…';
 try{
  const response=await fetch('/api/model/probe',{method:'POST',headers:{'X-WORLDTRACE-TOKEN':token}});
  const data=await response.json().catch(()=>({detail:'Invalid provider response'}));
  if(!response.ok)throw Error(data.detail||'HTTP '+response.status);
  out.textContent='REAL INFERENCE VERIFIED · '+String(data.returned_model||data.requested_model)+
   ' · Mission planning still unverified.';
  $('metricModel').innerHTML='LIVE<span class="metric-unit">API</span>';
 }catch(e){
  if(/403|authorization|token/i.test(e.message))app.missionToken=null;
  out.textContent='NOT VERIFIED · '+e.message;
 }finally{btn.disabled=false}
};

for(const [role,id] of multiFields){
 $(id).addEventListener('change',()=>{
  if(app.guidedDemoFiles){app.guidedDemoFiles=null;$('guidedDemoStatus').textContent='Guided demo cleared; using your selected files instead.'}
 });
}

$('loadSavedAgentMissions').onclick=async()=>{
 $('agentLoadStatus').textContent='Private UM- history requires the WORLDTRACE operator token; public demos do not.';
 const token=privateToken();
 if(!token){$('agentLoadStatus').textContent='Private history not loaded (no operator token). To try Agent Workforce without a key, click Run public supplier demo.';return;}
 try{
  const rows=await api('/api/unified-missions',{headers:{'X-WORLDTRACE-TOKEN':token}});
  const complete=await Promise.all(rows.slice(0,10).map(r=>api('/api/unified-missions/'+encodeURIComponent(r.id),{
   headers:{'X-WORLDTRACE-TOKEN':token}})));
  for(const data of complete){
   if(!app.unifiedMissions.some(m=>m.id===data.id)){
    app.unifiedMissions.push({id:data.id,goal:data.goal,created:data.created,data});
   }
  }
  renderAgentWorkforce();
  $('agentLoadStatus').textContent=complete.length+
    ' private UM- mission(s) loaded. Public demos remain available in this browser tab.';
  $('agentRoleDetail').innerHTML='<h2>Saved missions loaded</h2><p>'+complete.length+' private UM- mission records available. Choose a mission above, then inspect a role.</p>';
 }catch(e){
  if(/403|authorization|token/i.test(e.message))app.missionToken=null;
  $('agentLoadStatus').textContent='Private mission load failed: '+e.message;
  $('agentRoleDetail').textContent='Could not load saved mission evidence: '+e.message;
 }
};

async function loadUnifiedAuditList(){
 const token=privateToken();if(!token)return;
 const select=$('auditUnifiedMission');
 try{
  const rows=await api('/api/unified-missions',{headers:{'X-WORLDTRACE-TOKEN':token}});
  select.innerHTML='<option value="">Choose saved unified mission</option>'+rows.map(r=>
   '<option value="'+safe(r.id)+'">'+safe(r.id+' · '+r.status.replaceAll('_',' '))+'</option>').join('');
  if(app.selectedUnified?.startsWith('UM-')&&rows.some(r=>r.id===app.selectedUnified)){
   select.value=app.selectedUnified;
   await showUnifiedAudit(app.selectedUnified,token);
  }else{
   $('auditUnifiedResult').textContent=rows.length?'Select a saved mission to inspect its evidence.':'No saved unified missions found.';
  }
 }catch(e){$('auditUnifiedResult').textContent='Cannot load private evidence: '+e.message}
}
async function showUnifiedAudit(id,providedToken){
 if(!id)return;
 const token=providedToken||privateToken();if(!token)return;
 try{
  const data=await api('/api/unified-missions/'+encodeURIComponent(id),{
    headers:{'X-WORLDTRACE-TOKEN':token}});
  const verified=data.trace_verified&&data.report_verified;
  const verdict=verified?'STORED TRACE & REPORT HASHES VALID':'INTEGRITY CHECK FAILED';
  const trace=(data.trace||[]).map(e=>'<div class="ledger-row"><div><strong>'+safe(e.role)+'</strong><div class="muted">'+safe(e.action.replaceAll('_',' '))+'</div></div><div class="ledger-payload">'+safe(JSON.stringify(e.details))+'<div class="muted">SHA-256 '+safe(e.hash)+'</div></div></div>').join('');
  const reviews=(data.decisions||[]).map(d=>'<div class="ledger-row"><strong>Human '+safe(d.decision.replaceAll('_',' '))+'</strong><div class="ledger-payload">Action '+safe(d.action_index)+' · '+safe(d.reviewer)+' · '+safe(d.created)+'</div></div>').join('');
  const executions=(data.sandbox_executions||[]).map(x=>'<div class="ledger-row"><strong>Sandbox verification · '+(x.verified?'PASS':'FAIL')+'</strong><div class="ledger-payload">Before '+safe(x.before_count)+' → After '+safe(x.after_count)+' · Added '+safe(x.added_records)+' hashed records · Before SHA '+safe(x.before_digest)+' · After SHA '+safe(x.after_digest)+'</div></div>').join('');
  $('auditUnifiedResult').innerHTML='<div class="ledger-verify '+(verified?'':'bad')+'">'+safe(verdict)+'</div>'+
   '<p>'+safe(data.id)+' · '+safe(data.goal)+'</p>'+trace+
   '<h3>Human review decisions</h3>'+(reviews||'<p>No human decisions recorded.</p>')+
   '<h3>Approved sandbox execution</h3>'+(executions||'<p>No approved corrective execution yet.</p>')+
   '<p class="muted">Local SQLite, not independently anchored. Does not prove real-world change; no production write.</p>';
 }catch(e){$('auditUnifiedResult').textContent='Unable to inspect saved evidence: '+e.message}
}
$('loadUnifiedAudit').onclick=loadUnifiedAuditList;
$('auditUnifiedMission').onchange=e=>showUnifiedAudit(e.target.value);

$('loadMissionIntoOutcome').onclick=()=>importLatestUnifiedEvidence();
async function importLatestUnifiedEvidence(){
 let entry=app.unifiedMissions.find(m=>m.id===app.selectedUnified)||app.unifiedMissions[0];
 try{
  if(!entry){
   const token=privateToken();if(!token)return;
   const rows=await api('/api/unified-missions',{headers:{'X-WORLDTRACE-TOKEN':token}});
   if(!rows.length){$('outcomeImportedStatus').textContent='No unified mission yet. Start the guided demo in Mission Control first.';route('deliverables');return}
   const data=await api('/api/unified-missions/'+encodeURIComponent(rows[0].id),{
     headers:{'X-WORLDTRACE-TOKEN':token}});
   entry={id:data.id,goal:data.goal,created:data.created,data};
   app.unifiedMissions.unshift(entry);
  }
  // Refresh from protected storage so approvals and demo executions are included.
  let data=entry.data;
  if(entry.id.startsWith('UM-')){
   const token=privateToken();if(!token)return;
   data=await api('/api/unified-missions/'+encodeURIComponent(entry.id),{
     headers:{'X-WORLDTRACE-TOKEN':token}});
   entry.data=data;
  }
  const lines=['Mission: '+entry.id,'Instruction: '+entry.goal,'Result: '+data.status,
    'Data mode: '+data.mode,'Observed uploaded file checks:'];
  for(const item of data.observations||[]){
   lines.push('- '+item.file_name+' ('+item.tool+'): '+item.status+'; '+summarizeObservation(item)+
    '; SHA-256 '+item.sha256);
  }
  for(const check of data.cross_checks||[]){
   lines.push('Cross-file check: '+check.name+' · '+(check.matched?'MATCH':'MISMATCH'));
  }
  for(const decision of data.decisions||[]){
   lines.push('Human review: '+decision.decision+' on action '+decision.action_index);
  }
  for(const run of data.sandbox_executions||[]){
   lines.push('ISOLATED DEMO FIX (no production change): '+run.added_records+' hashed rows applied; before '+run.before_count+
    ' → after '+run.after_count+'; verification '+(run.verified?'passed':'failed')+
    '; before digest '+run.before_digest+'; after digest '+run.after_digest);
  }
  lines.push('Audit trace verified: '+String(data.trace_verified??'not reverified in tab'));
  lines.push('Report digest verified: '+String(data.report_verified??'not reverified in tab'));
  lines.push('LIMITATIONS: local inspection only; demo repair affects isolated SQLite, not customer systems.');
  $('outcomeGoal').value=('Produce a source-linked resolution and verification package: '+entry.goal).slice(0,1500);
  $('outcomeDomain').value=(data.observations||[]).some(x=>x.tool==='etl_compare')?'data_quality':
    (data.observations||[]).some(x=>x.tool==='network_inspect')?'api_incident':'supplier_onboarding';
  $('outcomeEvidence').value=lines.join('\n').slice(0,12000);
  $('outcomeImportedStatus').textContent='Imported mission '+entry.id+' into delivery request. Review evidence, then press Produce verified delivery package. No new real-world actions will execute.';
  route('deliverables');
 }catch(e){$('outcomeImportedStatus').textContent='Could not load evidence: '+e.message;route('deliverables')}
}


async function runPublicDemoOperation(url){
 const res=await fetch(url,{method:'POST'});
 const data=await res.json().catch(()=>({detail:'Invalid demo response'}));
 if(!res.ok)throw Error(data.detail||'HTTP '+res.status);
 return data;
}
function renderPublicGuidedDemo(data){
 const id='PUBLIC-DEMO-'+data.demo_id.slice(0,8);
 app.publicDemoSession=data;
 const existing=app.unifiedMissions.find(m=>m.id===id);
 const item={id,goal:data.instruction,created:new Date().toISOString(),
             data:{...data,goal:data.instruction,status:data.status}};
 if(existing)existing.data=item.data;else app.unifiedMissions.unshift(item);
 app.selectedUnified=id;renderAgentWorkforce();
 const verified=data.status==='VERIFIED_SANDBOX';
 const step=data.status==='REVIEW_NEEDED'?'<button id="approvePublicDemo" class="run-btn secondary-run" type="button">✓ Approve isolated demo correction →</button>':
  data.status==='APPROVED_SANDBOX_ONLY'?'<button id="executePublicDemo" class="run-btn secondary-run" type="button">▶ Execute approved SQLite correction & re-verify →</button>':
  '<div class="sandbox-verified"><strong>VERIFIED — ISOLATED DEMO ONLY</strong><p>Actual SQLite target changed from '+data.initial_target_rows+' to '+data.current_target_rows+' hashed records. '+data.rows_added+' inserted; source and target hashes now match.</p><small>Before '+safe(data.before_sha256)+' · After '+safe(data.after_sha256)+'</small></div><button id="downloadPublicReceipt" type="button" class="run-btn secondary-run">↓ Download real demo resolution receipt</button>';
 const trace=data.trace.map(e=>'<div class="public-trace-row"><strong>'+safe(e.role)+'</strong><span>'+safe(e.action.replaceAll('_',' '))+'</span><small>'+safe(e.hash.slice(0,16))+'…</small></div>').join('');
 $('publicDemoOutput').innerHTML='<div class="public-demo-facts"><div><small>SUPPLIED (SYNTHETIC) SOURCE</small><strong>'+data.source_rows+'</strong></div><div><small>INITIAL TARGET</small><strong>'+data.initial_target_rows+'</strong></div><div><small>MISSING RECORD</small><strong>'+safe(data.missing_ids.join(', '))+'</strong></div></div>'+
 '<div class="human-result"><div class="human-result-head"><strong>Mission result</strong><span class="run-status '+(verified?'passed':'finding')+'">'+safe(data.status.replaceAll('_',' '))+'</span></div>'+
 '<p>'+safe(data.instruction)+'</p><p>'+safe(verified?'After-state rechecked against the expected source hashes.':'The CSV parser found a missing supplier record. A correction is proposed but has not been applied until the separate approval and execution steps.')+'</p>'+
 '<div class="human-result-note">No Meta inference · Synthetic inputs only · No raw customer files · No external writes</div></div>'+
 step+'<button type="button" class="tiny-btn" id="publicDemoAgents">◉ Inspect real stage evidence in Agent Workforce</button>'+
 '<details class="public-demo-trace"><summary>View '+data.trace.length+' recorded execution stages · SHA chain '+(data.trace_verified?'VALID':'INVALID')+'</summary>'+trace+'</details>';
 $('publicDemoAgents').onclick=()=>route('agents');
 if($('approvePublicDemo'))$('approvePublicDemo').onclick=async()=>{
  const btn=$('approvePublicDemo');btn.disabled=true;btn.textContent='Recording demo approval…';
  try{renderPublicGuidedDemo(await runPublicDemoOperation('/api/public-demo/'+encodeURIComponent(data.demo_id)+'/approve'))}
  catch(e){btn.disabled=false;btn.textContent='Try approval again';$('publicDemoOutput').insertAdjacentHTML('afterbegin','<p class="error">Approval failed: '+safe(e.message)+'</p>')}
 };
 if($('executePublicDemo'))$('executePublicDemo').onclick=async()=>{
  if(!window.confirm('Execute the approved correction ONLY on this short-lived synthetic in-memory SQLite demo? No production files will be touched.'))return;
  const btn=$('executePublicDemo');btn.disabled=true;btn.textContent='Executing sandbox repair and re-querying state…';
  try{renderPublicGuidedDemo(await runPublicDemoOperation('/api/public-demo/'+encodeURIComponent(data.demo_id)+'/execute'))}
  catch(e){btn.disabled=false;btn.textContent='Retry sandbox execution';$('publicDemoOutput').insertAdjacentHTML('afterbegin','<p class="error">Demo execution failed: '+safe(e.message)+'</p>')}
 };
 if($('downloadPublicReceipt'))$('downloadPublicReceipt').onclick=()=>{
  const lines=['# WORLDTRACE — Public Guided Demo Resolution Receipt','',
    'Scenario: synthetic supplier onboarding','Mission: '+data.instruction,
    'Approved: '+data.approved,'Verified in isolated in-memory SQLite: '+data.verified,
    'Missing supplier ID: '+data.missing_ids.join(', '),
    'Source records: '+data.source_rows,
    'Target before: '+data.initial_target_rows,'Target after: '+data.current_target_rows,
    'Hashed records added: '+data.rows_added,
    'Before-state SHA-256: '+data.before_sha256,'After-state SHA-256: '+data.after_sha256,
    'Audit trace hash chain valid: '+data.trace_verified,
    'External writes: 0','Production records modified: false',
    'No Meta model call; this is a deterministic synthetic sandbox demonstration.',
    '','## Execution evidence'];
  for(const e of data.trace)lines.push('- '+e.role+' / '+e.action+' / SHA '+e.hash);
  downloadMarkdown(lines.join('\n')+'\n','WORLDTRACE-public-demo-resolution.md');
 };
}
$('startPublicDemo').onclick=async()=>{
 const button=$('startPublicDemo');button.disabled=true;button.textContent='Creating isolated demo session…';
 try{
  const data=await runPublicDemoOperation('/api/public-demo/start');
  renderPublicGuidedDemo(data);
 }catch(e){$('publicDemoOutput').innerHTML='<p class="error">Public demo unavailable: '+safe(e.message)+'</p>'}
 finally{button.disabled=false;button.textContent='▶ Start another fresh guided demo →'}
};
