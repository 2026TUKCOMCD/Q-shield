# Scan Score Criteria

This document describes how dashboard scores are computed in the current codebase.

## PQC Readiness Score (0-10)
Source: `backend/app/tasks.py:_calculate_pqc_score`

Inputs:
- `total_vulnerabilities` from SAST
- `total_vulnerable` from SCA

Formula:
- `total_issues = SAST.total_vulnerabilities + SCA.total_vulnerable`
- If `total_issues == 0` -> score = `10`
- Else score = `max(1, 10 - (total_issues // 5))`

Notes:
- Config scanner findings are not included in PQC readiness score.
- Score is integer 1-10.

## Heatmap Risk Score (per file, 0-10)
Source: `backend/app/tasks.py:_build_heatmap_tree`

Per file:
- `severity_score = min(10, (HIGH * 3) + (MEDIUM * 2) + (LOW * 1))`
- Only SAST findings are counted in the heatmap.

Per folder:
- The folder risk score is the **maximum** risk score of its children.

API conversion:
- `backend/app/routes/scans.py:_convert_heatmap_node`
- If `risk_score <= 1.0`, it is multiplied by `10.0` (legacy scaling).

## Risk Level Legend (frontend)
Heatmap:
- `frontend/src/services/heatmapService.ts:getRiskLevel`
- `CRITICAL`: >= 8.0
- `HIGH`: >= 5.0
- `MEDIUM`: >= 3.0
- `LOW`: > 0
- `SAFE`: 0

Inventory list:
- `frontend/src/components/InventoryTable.tsx:getRiskColor`
- `High`: >= 8.0
- `Medium`: >= 5.0
- `Low`: < 5.0

Inventory detail:
- `frontend/src/pages/InventoryDetail.tsx:getRiskConfig`
- Uses the same 8.0 / 5.0 thresholds.

## Inventory Risk Score (current behavior)
Source: `backend/app/routes/scans.py:_build_inventory_assets`
- `riskScore` is currently hard-coded to `5.0` for inventory assets.
- This is a placeholder and not derived from SAST/SCA/Config findings.
