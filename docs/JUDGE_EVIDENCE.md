# WORLDTRACE | Judge Evidence & Reproducibility Pack
**Meta Global AI Developer Hackathon · Startups track · candidate 2026-11-02**

## One-line product thesis

**WORLDTRACE is an approval-gated operational exception resolver: it investigates uploaded evidence, records proposed actions, executes only bounded authorized sandbox changes, and proves or refuses the after-state with linked trace evidence.**

### What makes this more than an analysis dashboard?

In the working supplier example, the user can inspect a **real SQLite state change** that moves two target records to three under explicit approval and after-state checks. In the adversarial counterexample, the user can **approve** a change but the execution policy still **rejects it** because an existing supplier value conflicts with the source. No production records are edited.

This is not general-purpose live enterprise remediation, multiple independent model agents, or an externally attested audit chain.

## Demonstration matrix

| Case | Initial data | Action | Expected independently observed result |
|---|---|---|---|
| Positive: missing supplier record | Source A1/A2/A3; target A1/A2 | Explicit approval, then isolated SQLite insert | 2→3, after-state equals source hashed snapshot, SHA audit valid |
| Negative: unsafe conflicting record | Source A1=Alpha, target A1=Altered, and A3 missing | Explicit approval followed by guarded execution attempt | Blocked unsafe conflict, target stays 2, no inserts, refusal audit valid |
| Authorization boundary | Approved action not yet recorded | Attempt execution | 409, no write |
| Replay boundary | Corrective action already completed or rejected | Attempt execution again | 409, no repeat write |
| Unrecognized demo session | Arbitrary invalid token | Fetch/approve/execute | 404 |
| Unauthorized Meta analysis | No private mission token | Attempt protected model inference | 403, no provider call |

## Reproducibility: local, no Meta credits

```powershell
cd C:\Users\acer\Downloads\WORLDTRACE-CLEAN
git pull --ff-only origin main
python -m pytest -q
python scripts/demo_resolution.py
python scripts/judge_benchmark.py
git status
```

The benchmark prints JSON with named pass/fail checks. The CI workflow runs the same benchmark after pytest and one-command demo.

**Method limitation:** The benchmark contains two *fixed, synthetic* supplier datasets; it is an implementation regression/safety demonstration, not a statistically generalizable model evaluation, security audit, or measured customer ROI.

## How to reproduce in browser (without keys)

1. Open https://worldtrace.onrender.com/ and wait for the latest Render deployment to become Live.
2. Launch public guided supplier demo, inspect discrepancy, approve, execute, inspect trace and receipt.
3. Start **Adversarial challenge**, approve, attempt execute, confirm blocked, target unchanged, and download refusal evidence.
4. Inspect recorded stage evidence in Agent Workforce. The six role cards describe sequential backend responsibilities; they are not six independently hosted LLM workers.

## Optional live Meta reasoning — separate proof required

1. Configure official provider credentials in Render Environment, **never in source or chat**.
2. Use Mission Control **Test real inference connection** behind the private WORLDTRACE operator token.
3. Capture an **actual provider response ID and model name**, not just a configured status.
4. On a synthetic public-demo mission, run protected **Run REAL Meta evidence assessment**, then show the trace event for **Meta Mission Commander** and reference-grounded hypotheses.
5. Confirm model output remains advisory; a human approval and separate deterministic correction gate are still required.

**Previous observation:** Baseten returned HTTP 403; $100 awarded hackathon credits were not visible in the selected organization. Therefore successful real inference has NOT been established. Provider permissions and credits are an external dependency. Mocked model-contract tests do not prove API access or LLM quality.

## Challenge positioning: official rubric, not invented scores

- **Impact — 30%:** Clear supplier onboarding workflow and risk of unverified correction. No independent market/customer results yet; don't claim adoption.
- **Meta AI tooling — 25%:** Optional Muse Spark Open inference code and provenance validation. Actual hosted inference remains to be demonstrated; no claim of model superiority without a comparable evaluation.
- **Technical depth — 20%:** Bounded parsers, mandatory approvals, replay protection, isolated SQLite write transaction with after-state checks, SHA-256 traces, positive/negative tests.
- **Demo — 25%:** Demonstrate both the successful fix and the intentional refusal, with a short video and clear screen evidence. Video has to be recorded and submitted by the participant.

## Truth boundaries, security and operations

- API uses a **shared operator secret**, not production authentication, per-user RBAC, or multi-tenant isolation.
- Self-service public demo stores short-lived in-memory synthetic data. Explicitly saved private mission summaries use local SQLite on a filesystem that might be wiped by Render restart/redeploy.
- Uploaded evidence is parsed locally and bounded; opt-in derived results may include identifiable values. Never use confidential or real customer evidence in the public prototype.
- The audit chain provides application-local tamper detection; it is not anchored externally, cryptographically signed, or independent of application administrators.
- Meta prompts can include the user's goal/instruction and sanitized counts, even though raw file contents are not sent. Do not include secrets in goals.
- No external production connector actions, verified financial ROI, independently measured model benchmark, enterprise reliability guarantee, or customer acquisition evidence.

## Final release gates

1. Latest full test suite and benchmark pass on exact release commit.
2. GitHub Actions green for exact commit; latest Render deployment and backend pass live smoke checks.
3. Real Meta provider permission and inference response verified **before describing model execution as successful**.
4. 3-minute demo video available at an independently accessible URL.
5. Startup Track submission portal fields completed, official consent reviewed, and successful submission receipt saved.
6. Save exact SHA and links for reproducibility. Submit before official deadline.

If Meta inference remains inaccessible, be truthful about the limitation rather than supplying fabricated outputs or an untested proxy model. Such a submission is substantially weaker for the Meta-tooling criterion.
