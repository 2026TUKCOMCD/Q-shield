# Scan Score Criteria

This document describes how dashboard scores are computed in the current codebase.

## PQC Readiness Score (0-10)
Source: `backend/app/tasks.py:_calculate_pqc_score`

Inputs:
- SAST and SCA findings

Weights:
- Severity: `CRITICAL=4.0`, `HIGH=3.0`, `MEDIUM=2.0`, `LOW=1.0`, `INFO=0.5`
- Algorithm weight:
  - Public key (`RSA`, `ECC/ECDSA`, `DSA`, `DH`): `1.6`
  - Weak hash (`MD5`, `SHA-1`): `1.3`
  - Symmetric (`AES`, `ChaCha`): `1.0`
  - Unknown: `1.0`

Formula:
- For each finding: `risk_points = severity_weight * algorithm_weight`
- `weighted_total = sum(risk_points)` for SAST + SCA
- If `weighted_total <= 0` -> score = `10`
- Else `penalty = min(9.0, weighted_total / 3.0)`
- Score = `int(max(1.0, 10.0 - penalty))`

Notes:
- Config scanner findings are not included in PQC readiness score.
- Score is integer 1-10.

## Heatmap Risk Score (per file, 0-10)
Source: `backend/app/tasks.py:_build_heatmap_tree`

Per file:
- Sum of `severity_weight * algorithm_weight` across SAST findings.
- `severity_weight` and `algorithm_weight` are the same as PQC readiness score.
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
Source: `backend/app/tasks.py:_extract_inventory_table` + `backend/app/routes/scans.py:_build_inventory_assets`
- Each algorithm entry gets a `risk_score` computed from SAST findings:
  - `risk_score = min(10, sum(severity_weight * algorithm_weight))` for that algorithm
- API uses `entry.risk_score` when building inventory assets.
