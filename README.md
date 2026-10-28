# WORLDTRACE ◈

**Autonomous Execution. Verifiable Outcomes.**

> A verifiable agent-execution prototype for the Meta Global AI Developer Hackathon 2026. Startup track · Push the Frontier.

WORLDTRACE transforms an enterprise mission into a **recorded execution** involving document, mail, network, ETL, database, API, performance, middleware, and legacy-record checks. It generates a genuine Markdown evidence report with a hash-chained event log. Model-driven planning is supported **only after a real Meta-compatible inference endpoint is configured**.

## Important: real vs planned

| Capability | Verified implementation |
|---|---|
| Mission Control web dashboard | Yes, locally served |
| Nine local enterprise analysis/test tool functions | Yes, using synthetic fixtures |
| Concurrent/background autonomous service | Background thread per mission (prototype only; not durable production queue) |
| Events / task state persistence | Yes, SQLite |
| Per-mission SHA-256 audit chain | Yes; application DB is not immutable or externally anchored |
| Actual downloadable evidence report | Yes, Markdown |
| Human review of recovery proposals | Protected API records one-time approve-for-manual-follow-up or reject decision in audit chain; no automated repair |
| Meta-model-driven tool selection | Optional via configured real OpenAI-compatible inference endpoint; **not verified without provider access** |
| Browser automation, real email sending, hosted mainframes | Not implemented |
| Actual repair of production systems | Not implemented; prohibited in this demo |
| Production-grade access control / approvals | Not implemented; model mission submission is protected by a private header token, but local runs, mission listing and reports are public; synthetic demo only |
| Industry-scale enterprise testing | Not claimed |

### Why this matters

A frontend status animation is not execution proof. WORLDTRACE stores tool results, timestamps, assertions, task states, evidence chain hashes and actual artifacts. Sample fixtures are intentionally defective so the system detects real findings rather than reporting invented success.

## Quickstart

Requires Python 3.11+.

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Open **http://127.0.0.1:8000**. The local workflow runs with zero API credentials, using synthetic test data and deterministic keyword-based tool routing (broad or ambiguous missions run all nine tools). **This mode is not model-driven agent autonomy.** Use **META MODEL** only after configuring real inference.

To verify:

```bash
pip install pytest
pytest -q
```

API docs: `http://127.0.0.1:8000/docs`. Health: `http://127.0.0.1:8000/healthz`.

## Optional Meta model integration

The planner sends the mission and 9 allowlisted tool IDs to a real configured OpenAI-compatible chat completions endpoint. The real model selects a distinct subset of tools. The backend checks and executes the plan, then deterministically verifies the returned fixture evidence. A model failure causes an explicit error; there is no silent rule-based fallback presented as AI.

Set environment variables (do not commit keys):

```text
WORLDTRACE_MODEL_BASE_URL=https://YOUR-VERIFIED-PROVIDER/v1
WORLDTRACE_MODEL_API_KEY=YOUR_PRIVATE_KEY
WORLDTRACE_MODEL_NAME=meta-models/muse-spark-open-1026
WORLDTRACE_MODEL_PROVIDER=your-provider-name
WORLDTRACE_MISSION_TOKEN=GENERATE_A_LONG_RANDOM_SECRET
```

**The endpoint format, model name, authorization method, inference credit access, and model usage must be verified with your actual provider.** The dashboard asks for `WORLDTRACE_MISSION_TOKEN` only when starting a model-mode mission; it is held in tab memory, not in localStorage. Never enter the provider API key in the dashboard. A configured endpoint is NOT evidence of successful inference. This example is not proof of successful connectivity. Meta Model API may require a payment method even when credits have been granted. Do not incur charges without understanding billing. This prototype does not ship with credentials.

## Standalone specialist workspaces

Agent Workforce and Enterprise Tools cards now open the corresponding tool's own interactive workspace rather than merely pre-populating a generic mission. Every module explains its approved sample input, exact analysis sequence, limits, live Run action, real backend output and prior recorded runs. The API uses `GET /api/tools/{tool_id}/workspace`, `POST /api/tools/{tool_id}/runs`, `GET /api/tools/{tool_id}/runs` and `GET /api/tool-runs/{run_id}`. The sample-run action remains **bounded synthetic fixture analysis**; a separate authenticated upload action now inspects supported user files in memory. Neither is a production connector. Synthetic standalone tool runs are persisted in local SQLite and are not the same as hash-chained multi-tool mission events. On free Render, this storage remains ephemeral. These public demo endpoints have no user-level authentication.

## Human review API (bounded)

`POST /api/missions/{mission_id}/reviews` requires the `X-WORLDTRACE-TOKEN` header, and a JSON body with `tool`, `decision` (`approve_for_manual_followup` or `reject`), `reviewer`, and optional `note`. This records a one-time decision about an existing recovery proposal after the synthetic mission has completed. `GET /api/missions/{mission_id}/reviews` also requires the private token. This does not execute remediation or authenticate individual users, and the token must never be committed or shared. The visual reviewer interface is not implemented yet.

## Execution flow

```text
User mission
    ↓
Deterministic mission-scoped local plan OR configured Meta model-driven plan
    ↓
Validate tool ID allowlist and boundaries
    ↓
Execute specialist tools against controlled local synthetic fixtures
    ↓
Record each tool's actual result and pass/finding/error
    ↓
Deterministic final verification + SHA-256 chained log
    ↓
Download real Markdown mission evidence report
```

## Sample outputs

- `pdf_inspect` detects an unsigned supplier document.
- `network_inspect` detects an HTTP 503 response in the synthetic HAR.
- `etl_compare` finds a missing record.
- `database_check` identifies pending onboarding records.
- `api_virtualize` finds a deliberately failing mock contract.
- `middleware_test` detects duplicate message IDs.

These are real computations over included generated **synthetic** files, not claims about a real company or live integration.

## Security and scope

- File paths restricted to the approved sample directory.
- The database audit uses read-only SQL, with a fixed query.
- Model-selected tool identifiers must be on the allowlist.
- External side effects, sending emails, production system edits and destructive actions are absent.
- All included business entities, test data, network addresses and documents are synthetic.
- Public routes still permit local synthetic missions, history listing and evidence report access without login. Never use real production information or customer files here.
- Model mission POST requires the private `X-WORLDTRACE-TOKEN` request header and a matching `WORLDTRACE_MISSION_TOKEN` environment variable. This is narrow API protection, not a full user authentication/authorization system.
- Audit chaining is tamper-evident only while the chain verifier and persisted data remain trusted; no cryptographic signatures or external anchoring are provided.

## Competition honesty

This is an initial hackathon build foundation, **not a completed fully autonomous robotics product**. Successful real Meta model inference, operational reliability, production security governance, richer execution/replanning, visual evidence analysis, enforced human approval gates, and external integrations are outstanding build stages and must be tested before making submission claims. Startups track reward details and rules should be checked against the organizer's latest published materials.

## Deployment

Includes `render.yaml` (Free instance configuration) and `Procfile`. Render's ephemeral storage can lose SQLite state on restart or deployment; use persistent backing storage before claiming durable persistence. Free-tier availability and limits are subject to provider policy.

## License

MIT. Do not incorporate third-party proprietary code or copyrighted assets without rights. Original WORLDTRACE code is independent of Phaze AI and ACCELQ.

## v11 — Multi-file mission execution

The Multi-File Mission page accepts one instruction plus approved user files (PDF, EML, HAR, paired source/target CSV, API JSON, middleware JSON, or legacy TXT). An authenticated POST to `/api/multi-file-missions/run` executes bounded real-file parsers, correlates HAR failures with simulated API status where applicable, records a hash-linked stage trace, and returns an integrity-hashed Markdown report for download. No raw files are saved in the mission history; do not use confidential customer data in this public prototype. Each file is limited to 2 MiB, combined input to 8 MiB.

**Honest scope:** v11 is a deterministic multi-file engine, not six independent Meta AI agents or general autonomous problem solving. Stage names describe responsibilities. No real-world repairs, production connections or Meta inference occur on this route. The goal describes the output; it is not used to execute arbitrary shell commands. Meta-backed planning awaits a verified eligible inference provider.

## v12 — Unified Mission Control and distinct Agent Workforce

The main Mission Control now directs **Start unified mission** into the authenticated, real-file multi-input flow. The old synthetic-fixture mission composer is explicitly marked as optional and separate. The standalone **Multi-File Mission** sidebar entry has been removed to avoid duplicate workflows; the processing route remains available under the Mission Control journey.

The Agent Workforce no longer duplicates the nine tool cards. It shows six distinct operational responsibilities (Research, Security, Execution, Verification, Builder, Delivery) **linked to recorded stages of a completed file-backed mission**. A user can inspect each role's actual stage records, findings count, and trace, then navigate back to that mission's result and download its real Markdown report. Enterprise Tools still lists genuine file/fixture parsers used by the execution layer.

**Limitations:** The unified-file mission remains deterministic, not six autonomous model-backed AI agents. Its completed result and agent workforce view are kept in **browser-tab memory only** for up to five recent operations, so refreshing the page loses that specific result view. No uploaded file content is stored in the public mission listing. This work does not resolve Meta inference access, long-running durable tasks, or external remediation. The old sample mission listing is independent of unified file-backed sessions.

## v13 — Operator-controlled saved missions, review, and inference diagnostics

On **Unified Mission Control**, checking **Save derived findings and report for later review** explicitly opts in to SQLite persistence of the completed mission report, derived findings, stage trace and checks. Raw uploaded input files are never persisted by this feature. **Load saved** retrieves up to 30 recent records through token-protected `GET /api/unified-missions` and `GET /api/unified-missions/{id}`. The browser can reopen and redownload a completed report. Without this checkbox, v12's transient response behavior is preserved.

In **Human Review**, **Load saved mission review queue** allows a private operator to record a one-time `approve_manual_followup` or `reject` disposition per proposed action through `POST /api/unified-missions/{id}/decisions`. These decisions **never execute a fix**, change a customer record or trigger an outbound message. This is a shared operator secret, not a multi-user identity and permission system.

The **Test real inference connection (may use credits)** control sends an explicit, short, token-protected live chat-completion probe to the configured endpoint through `POST /api/model/probe`. It sends no uploaded files, mission goals, or private document content. It displays a successful status only after receiving an actual provider response; a configured key alone is not proof of inference. Provider access may require activated credits and billing. Do not press the probe until costs and credits are understood.

**Durability boundary:** Completed records are stored in local SQLite, but the free Render deployment filesystem is ephemeral. This is **not** a durable production queue, external database, recovery scheduler, crash-resumable execution, encrypted document vault or verified Meta agent orchestration. Reports may contain derived sensitive excerpts; opt in only for synthetic/non-confidential files.
