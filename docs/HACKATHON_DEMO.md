# WORLDTRACE — Hackathon Demo Runbook (3 minutes)

**Product:** Controlled operational exception resolution with verifiable before/after outcomes.

**Do not claim:** External production changes, six independently hosted AI agents, unrestricted self-repair, durable Render storage, or successful real Meta inference until the actual provider response is verified.

## Preflight

- Deploy newest main commit; confirm Render reports Live.
- On Windows, locally run `python -m pytest -q` and `python scripts/demo_resolution.py`.
- Chrome hard refresh `https://worldtrace.onrender.com/` with Ctrl+Shift+R.
- Use the **public, synthetic-only guided demonstration** for the main recorded demo; it does not need a secret API key.
- If real model access has been verified, optionally include a short segment showing model name, response provenance, grounded hypothesis and the host validation. If it still returns HTTP 403, do **not** present a fabricated provider result.

## Screen-by-screen script

### 0:00–0:25 — The business problem

**Screen:** Mission Control homepage → 'Launch guided resolution demo'.

**Say:** "Business onboarding failures can involve documents, APIs and missing records. Dashboards show alerts; WORLDTRACE is designed to connect an authorized investigation to a controlled, verifiable outcome. I'll demonstrate one full resolution in an isolated environment."

### 0:25–0:55 — Real analysis

**Screen:** Click 'Start complete guided demo (no login)'.

**Say:** "This is not prerecorded animation. WORLDTRACE generates two synthetic CSV inputs and runs the same bounded data reconciliation parser that powers real-file uploads. It detects three source records, two target records and missing supplier A3. The finding is tied to a recorded execution trace."

### 0:55–1:25 — Explicit human approval

**Screen:** The 'Approve isolated demo correction' action.

**Say:** "A finding does not give the agent permission to change a system. The proposed action is restricted to the isolated in-memory SQLite sandbox. The platform blocks execution until this separate approval is recorded."

**Action:** Click Approve. Point out updated state.

### 1:25–1:55 — Real scoped execution and re-verification

**Screen:** Click 'Execute approved SQLite correction & re-verify', confirm the scope prompt.

**Say:** "WORLDTRACE inserts exactly one missing hashed row into the isolated demo database. It then queries the resulting database state and checks that the target snapshot matches the source. We now have a before state of two rows, an after state of three, and a verified result. No production data or uploaded CSV has been modified."

### 1:55–2:20 — Actual trace and receipt

**Screen:** Expand the execution trace and download the resolution receipt.

**Say:** "Each recorded stage has a SHA-256 chained event. The downloaded receipt identifies the observed discrepancy, the approval, the executed sandbox change and the after-state digest. These hashes prove integrity of the recorded application evidence, not independent proof of any external business process."

### 2:20–2:45 — Agent responsibilities and specialist tools

**Screen:** 'Inspect real stage evidence in Agent Workforce' → click a role's 'Inspect role and evidence' button → briefly show Enterprise Tools.

**Say:** "Agent Workforce explains six distinct operational responsibilities. The tool layer performs bounded inspection; responsibility logs explain what was done. In local mode these are deterministic processing stages, not six separate model inference calls."

### 2:45–3:00 — Model integration status and conclusion

**If real Meta inference is verified:** Show the real provider response and the optional model-guided mission planning/evidence hypothesis trace.

**If Meta inference remains blocked:** Do not claim model success. Say: "The application also implements a guarded Muse Spark Open integration for role-based planning and evidence-referenced hypotheses, but provider permissions are still being verified, so this demonstration remains local."

**Finish:** "WORLDTRACE's design principle is simple: no claim of completion without an authorized action, observed after-state and traceable evidence."

## Local independent evidence

```powershell
cd C:\Users\acer\Downloads\WORLDTRACE-CLEAN
git pull --ff-only origin main
python -m pip install -r requirements.txt
python -m pytest -q
python scripts/demo_resolution.py
git status
```

The last command should show no local modifications. Never show private WORLDTRACE operator tokens, Baseten keys, personal documents, or billing account details in the video.

## Submission truth checklist

- [ ] Public demo succeeds in a fresh incognito browser.
- [ ] All automated tests pass.
- [ ] One-command acceptance prints verified before/after and duplicate prevention.
- [ ] Model provider status is backed by an actual response if making Meta-model claims.
- [ ] Repository and live demo URLs work without broken links.
- [ ] 3-minute walkthrough is recorded and audible.
- [ ] No confidential customer data, provider secrets or unsupported production claims appear.
