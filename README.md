# WORLDTRACE ◈
### One instruction. Controlled execution. Verifiable outcomes.

![WORLDTRACE geometric W brand mark](WORLDTRACE_Logo_HD_2048.png)

[🌐 Live prototype](https://worldtrace.onrender.com/) · [💻 Source code](https://github.com/Sraveena1992/WORLDTRACE) · [📖 API docs](https://worldtrace.onrender.com/docs) · [🩺 Health check](https://worldtrace.onrender.com/healthz)

**Meta Global AI Developer Hackathon 2026 · Startups track · Evidence-first operations prototype**

WORLDTRACE investigates operational exceptions from user-authorized evidence, runs allowlisted analysis tools, prepares reviewable actions, and demonstrates an **approval-gated correction with independent after-state checks in an isolated SQLite sandbox**.

> **Scope declaration:** This is a working prototype, not a production deployment or an unconditional autonomous AI system. Actual Meta Muse Spark Open inference code exists, but our Baseten provider request previously returned HTTP 403; successful production model inference must be verified before it is presented in judging. Local deterministic execution is clearly distinguished from real inference.

## 🎯 Signature scenario: a supplier onboarding mismatch

The user gives one instruction: *Investigate missing supplier records; propose a safe correction; require approval; execute only on the allowed system; prove the result.*

The guided scenario begins with **three source rows and two target rows**. WORLDTRACE observes that supplier `A3` is missing, creates a specific controlled correction proposal, requires an explicit human approval, and—only after a second explicit Execute action—inserts the missing **hashed** record into an **isolated demo SQLite database**. It queries the resulting state and verifies that target hashes match the source snapshot.

| Stage | Actual behavior | What is *not* claimed |
|---|---|---|
| Research | Inventory supplied files and their roles | No unrestricted online browsing |
| Security | Validate types, sizes, execution policy | Not enterprise-grade RBAC |
| Execution | Inspect actual PDF/CSV/HAR/EML/JSON/TXT bytes | No live enterprise connectors |
| Verification | Reconcile data, cross-check eligible inputs, SHA-256 trace | No independent proof of real-world truth |
| Builder | Produce a bounded corrective proposal | No arbitrary self-generated production code |
| Human Review | Record one-time approve/reject decision | Approval alone performs no repair |
| Authorized Sandbox Action | Insert missing hashed records inside isolated SQLite | Original CSV and production databases untouched |
| Re-verification | Query after-state, compare to original source hashes | No claim of external supplier approval |
| Delivery | Investigation report, post-action receipt, Markdown or ZIP package | No invented external business outcome |

Six functional role names reflect **recorded processing stages**, not six separate AI inference agents.

## ▶️ Reproduce the full demo in one command

Requires Python 3.11+, including Windows PowerShell.

```powershell
git clone https://github.com/Sraveena1992/WORLDTRACE.git
cd WORLDTRACE
python -m pip install -r requirements.txt
python scripts/demo_resolution.py
```

The script is self-contained: it uses temporary test storage and a local-only operator token. It does not call Meta inference or any production service. Expected proof includes:
- Unapproved action rejected.
- `A3` missing from source-to-target comparison.
- Human approval recorded.
- Isolated target changes from **2 → 3 hashed records**.
- Actual SQLite after-state rechecked against expected source digests.
- Original CSV remains unchanged; external writes are zero.
- Repeated execution rejected.
- Stored investigation report hash and stage event chain revalidated.

Run the automated suite:

```powershell
python -m pip install pytest
python -m pytest -q
```

## 🌐 Browser walkthrough

1. Open the [live app](https://worldtrace.onrender.com/). Enter **Mission Control → Start unified mission**.
2. Click **Load safe demo evidence and instruction**. This loads only synthetic browser-created CSVs, enables opt-in report storage, and leaves model planning disabled.
3. Click **Execute multi-file analysis**. Enter the private `WORLDTRACE_MISSION_TOKEN` (never the provider API key).
4. Inspect the actual CSV finding: source has 3 rows, target has 2, missing `A3`.
5. Click **Review and resolve in demo**. Approve the specific **CONTROLLED DEMO CORRECTION**.
6. Click **Execute approved demo correction & re-verify**. A second operator confirmation is required.
7. Confirm **Before 2 → After 3**, `verified=true`, and no external changes. Download the **verified demo resolution receipt**.
8. Open **Evidence Ledger**, load saved unified evidence and inspect the trace, approvals and before/after hashes.
9. Open **Agent Workforce**, load saved missions if needed and inspect each recorded responsibility (cards have drill-downs).
10. Open **Outcome Studio → Use latest unified mission evidence**, review the imported material and produce an additional ZIP package.

The live Render free-tier filesystem is **ephemeral**; stored missions can disappear on restart or redeployment. The local one-command demo does not depend on Render persistence.

## 🧩 Specialist tool capabilities

`pdf_inspect` extracts text and page metadata; `etl_compare` compares two actual CSVs by unique `id` records; `network_inspect` detects HTTP failures in user HAR archives; `email_inspect` inspects EML headers; `api_virtualize` evaluates local JSON mock contract statuses; `middleware_test` spots duplicate message IDs in JSON; `mainframe_contract` validates fixed-width TXT records.

`database_check` and `performance_probe` remain **local synthetic fixture tools only**. The Enterprise Tools page provides standalone diagnostics; Mission Control is the coordinated workflow. Uploaded files are limited to **2 MiB each**, combined **8 MiB**, and supported PDF extraction is limited to 50 pages without OCR.

## 🧠 Optional real Meta-model integration

The Meta Muse Spark Open model is available from hosted providers including Baseten. Once a genuinely authorized inference account is available:

```text
WORLDTRACE_MODEL_BASE_URL=https://inference.baseten.co/v1
WORLDTRACE_MODEL_NAME=meta-models/muse-spark-open
WORLDTRACE_MODEL_PROVIDER=Baseten
WORLDTRACE_MODEL_API_KEY=<private Baseten API key>
WORLDTRACE_MISSION_TOKEN=<separate private operator token>
```

**Never commit keys.** The Mission Control **Test real inference connection** control sends one explicit short request that might consume credits. When the **actual model** checkbox is selected for a unified mission, WORLDTRACE asks the hosted model to propose an exact, validated file execution order; after local file processing it requests a **second real inference response** for bounded, evidence-referenced root-cause hypotheses. This sends the user instruction and selected role names, followed by *sanitized tool statuses and counts*. Raw PDFs, raw CSV rows, and extracted document excerpts are not sent through these calls.

The backend rejects incomplete or unauthorized model plans and invented evidence references. On provider failure, the API returns an explicit error rather than silently pretending local rules were model reasoning. **A successful real Baseten call has not yet been verified in this deployment (HTTP 403 previously observed).** Mocked tests do not establish real provider access.

Hosted provider reference: [Meta documentation for Muse Spark Open](https://dev.meta.ai/docs/muse-spark-open/deploy).

## 🔐 Security, data and truth boundaries

- Upload and unified mission endpoints require the shared `X-WORLDTRACE-TOKEN`; this is **not** individual user authentication.
- Raw uploaded file bytes are processed within the request and not deliberately persisted by the unified upload API.
- **Optional** saved missions persist derived file results, report text, hashes and consented sandbox snapshots in local SQLite. Derived reports may contain user-provided IDs or snippets—**do not upload confidential, regulated or real customer data** to this public prototype.
- The demo sandbox persists **salted hashes of source and target CSV records**, not plaintext CSV content; it never modifies original uploaded files.
- The model cannot select unapproved tools, run shell commands, or authorize an external write.
- Every demo correction is gated by an explicit recorded approval and separate execution action. One-time execution and initial-state checks protect against accidental replay.
- SQL sandbox repair and verification run within one transaction; unsafe baseline differences or mismatched rows cause rejection.
- Stage hashes and report SHA-256 are verifiable **inside the application**, but are not cryptographically signed or externally anchored.
- No production durable job queue, external system adapter, email sending, browser automation, or enterprise access governance is claimed.

## 🛠️ Tech stack

Python · FastAPI · Pydantic · SQLite · pypdf · ReportLab · vanilla JavaScript · Render · GitHub

Project layout: `app.py` provides API endpoints; `worldtrace/multifile.py` coordinates real file processing and trace; `worldtrace/uploads.py` owns parsers; `worldtrace/unified_records.py` stores consented results; `worldtrace/sandbox_recovery.py` implements approval-gated sandbox repair; `worldtrace/agent.py` holds optional Meta-compatible inference; `static/` contains the interface; `tests/` holds regression tests.

## 🚧 Outstanding work / submission honesty

Full production-grade autonomy, durable hosted persistence, real customer-approved connectors, independently deployed AI workers, identity-based RBAC, and verified successful live Muse Spark Open inference are **not complete**. Hackathon results and prize placement cannot be guaranteed. We submit only behaviors demonstrated in the live application or reproducible command-line checks.

## License

[MIT](LICENSE). WORLDTRACE source code and branding are original to this project.
