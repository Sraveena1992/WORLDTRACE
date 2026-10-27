# WORLDTRACE | Mission Evidence Report

**Mission:** WT-4E7BB6C34C
**Goal:** Investigate why supplier onboarding has failed and produce evidence
**Execution mode:** local
**Verification:** needs-review

## Tool results
### Document Analyst — finding
```json
{
  "checks": {
    "signed": false,
    "supplier_name": true,
    "tax_id": true
  },
  "excerpt": "Supplier Onboarding Compliance Record\nSUPPLIER NAME: NORTHSTAR COMPONENTS\nTAX ID: NS-39012\nSIGNED: NO\nDOCUMENT STATUS: INCOMPLETE\n",
  "file": "supplier_check.pdf",
  "pages": 1,
  "pass": false,
  "sha256": "22d35eef396067b240e8c51f4ba396cab3042ca359f0d0bc252e368289d87e57"
}
```

### Communications Analyst — passed
```json
{
  "checks": {
    "mentions_onboarding": true,
    "reports_missing": true
  },
  "file": "supplier_notice.eml",
  "pass": true,
  "sender": "vendor@example.test",
  "subject": "Supplier onboarding documentation"
}
```

### Network Investigator — finding
```json
{
  "failure_count": 1,
  "failures": [
    {
      "ms": 2100,
      "status": 503,
      "url": "https://example.test/api/validate"
    }
  ],
  "finding": "HTTP failures detected",
  "pass": false,
  "total_requests": 2
}
```

### Data Integrity Agent — finding
```json
{
  "extra_ids": [],
  "mismatched_ids": [],
  "missing_ids": [
    "A03"
  ],
  "pass": false,
  "source_rows": 3,
  "target_rows": 2
}
```

### Database Auditor — finding
```json
{
  "access": "read-only SQL on approved sample database",
  "pass": false,
  "pending": 1,
  "rows": 2,
  "table": "suppliers"
}
```

### API Simulator — finding
```json
{
  "endpoint": "/api/onboarding/validate",
  "expected": 200,
  "mode": "local mock; no external API called",
  "pass": false,
  "simulated": 503
}
```

### Performance Engineer — passed
```json
{
  "p95_ms": 0.0032,
  "pass": true,
  "samples": 20,
  "target": "bounded in-process hashing only; not production service throughput"
}
```

### Integration Tester — finding
```json
{
  "duplicates": [
    "evt-001"
  ],
  "messages": 2,
  "mode": "local queue-fixture replay, not broker connected",
  "pass": false,
  "unique_ids": 1
}
```

### Legacy Systems Analyst — finding
```json
{
  "invalid_lines": [
    1,
    2
  ],
  "mode": "fixed-width file contract; not connected to actual mainframe",
  "pass": false,
  "records": 2
}
```

## Reliability notes
- Evidence comes from included synthetic LOCAL sample fixtures.
- A tool passing its assertion is not proof that an external enterprise environment was tested.
- Model mode requires a real working configured Meta-compatible inference endpoint.
- External writes, email sends, and production fixes are NOT performed by this build.