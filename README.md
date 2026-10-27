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
