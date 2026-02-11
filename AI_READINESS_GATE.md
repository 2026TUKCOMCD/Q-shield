# AI Readiness Gate (Findings)

Date: 2026-02-11

## Checklist

### Findings Schema
- Status: PASS
- Evidence:
  - Normalization + validation in `backend/app/tasks.py` lines 407-641.
  - Schema doc in `FINDINGS_SCHEMA.md`.
  - Test coverage in `backend/tests/test_findings_normalization.py`.

### Severity Consistency
- Status: PASS
- Canonical severities: `CRITICAL|HIGH|MEDIUM|LOW|INFO`
- Mapping table: `backend/app/severity_map.py` lines 5-32.
- Normalization uses canonical severity + score in `backend/app/tasks.py` lines 516-534.
- Tests: `backend/tests/test_severity_map.py`

### Dedup / Noise Control
- Status: PASS
- Dedup key: `(scanner_type, rule_id, file_path, line_start, line_end, evidence_hash)`
- Implementation: `backend/app/tasks.py` lines 481-502.
- Tests: `backend/tests/test_findings_dedup.py`

## Issues Found and Fixed (with locations)
1. Missing canonical severity mapping and numeric score.
   - Fixed in `backend/app/severity_map.py:5-32` and applied in `backend/app/tasks.py:516-534`.
2. No required-field validation for normalized findings.
   - Fixed in `backend/app/tasks.py:436-477`.
3. No dedup policy before DB persistence.
   - Fixed in `backend/app/tasks.py:481-502`.

## Remaining Issues
- None identified in this pass.

## Test Commands
```bash
python -m pytest
```
