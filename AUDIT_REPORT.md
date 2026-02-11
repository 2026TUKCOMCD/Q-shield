# Scanner Audit Report

Date: 2026-02-11

## Scope
Verify the three scanners (SAST, SCA, Config) for real detection behavior, output contracts, and backend integration. Identify gaps, apply minimal fixes, add tests, and provide an AI-readiness verdict.

## Architecture Map (Trigger → Execution → Persistence → API)
1. Trigger
- `POST /api/scans` enqueues the Celery task `run_scan_pipeline`.
- Source: `backend/app/routes/scans.py:196`.

2. Scanner pipeline
- Clone repo, analyze languages, select targets, run SAST/SCA/Config.
- Source: `backend/app/tasks.py:61`, `backend/app/tasks.py:66`, `backend/app/tasks.py:70`, `backend/app/tasks.py:75`, `backend/app/tasks.py:80`.

3. Normalization & persistence
- Inventory, heatmap, recommendations, and normalized findings persisted in one transaction.
- Source: `backend/app/tasks.py:88`, `backend/app/tasks.py:93`, `backend/app/tasks.py:94`, `backend/app/tasks.py:95`, `backend/app/tasks.py:97`, `backend/app/tasks.py:120`.

4. API responses
- Inventory/heatmap/recommendations read from snapshots and recommendations tables.
- Source: `backend/app/routes/scans.py:333`, `backend/app/routes/scans.py:404`, `backend/app/routes/scans.py:430`.

## Scanner Review

### SAST
Purpose and technique
- Static code scanning using AST (Python) and regex patterns (Python/JS/Java).
- Evidence: `3_scanner/scanners/sast/python_analyzer.py:7`, `3_scanner/scanners/sast/javascript_analyzer.py:1`, `3_scanner/scanners/sast/java_analyzer.py:6`, `3_scanner/scanners/sast/crypto_rules.py:4`.

Detects
- RSA/ECDSA key generation, weak hashes, and vulnerable imports for Python.
- RSA/ECC key generation and crypto library usage for JS/TS.
- RSA/ECDSA keypair/signature usage for Java.

Limitations
- Pattern-based detection only; no dataflow or semantic verification.
- Line-only de-duplication in Python can hide multiple issues on the same line.
- No key-size extraction or usage context beyond regex/AST matches.

### SCA
Purpose and technique
- Parses dependency manifests (package.json, requirements.txt, pom.xml, go.mod) and compares against a static PQC vulnerability list.
- Evidence: `3_scanner/scanners/sca/parsers.py:14`, `3_scanner/scanners/sca/scanner.py:15`, `3_scanner/scanners/sca/vulnerability_db.py:3`.

Detects
- Libraries in a curated PQC-unaware list with version thresholds.

Limitations
- Static list only; no CVE feeds or license checks.
- No transitive dependency resolution.

### Config
Purpose and technique
- Regex scanning for crypto/TLS settings and certificate analysis using OpenSSL.
- Evidence: `3_scanner/scanners/config/scanner.py:45`, `3_scanner/scanners/config/crypto_config_rules.py:3`.

Detects
- Outdated TLS versions, RSA/ECDSA/DHE ciphers, weak ciphers.
- Certificates with RSA/ECC keys if OpenSSL is available.

Limitations
- YAML structured parsing TODO remains; only regex matching is active.
- Config target selection is based on path keywords; may miss files like `secrets.yaml`.
- If OpenSSL is missing, cert analysis is silently skipped.

## Evidence of Real Scanning (Sample Outputs)

### SAST + SCA on `test_vulnerable_repo`
Command used
- `python -` (script in terminal, repo root)

Sample output (excerpt)
```json
{
  "sast": {
    "total_files_scanned": 3,
    "total_vulnerabilities": 12,
    "details": [
      {
        "file_path": "vulnerable_crypto.py",
        "vulnerabilities": [
          {
            "type": "rsa_key_generation",
            "line": 8,
            "severity": "HIGH",
            "algorithm": "RSA"
          },
          {
            "type": "weak_hash",
            "line": 21,
            "severity": "MEDIUM",
            "algorithm": "Weak Hash"
          }
        ]
      }
    ]
  },
  "sca": {
    "total_files_scanned": 2,
    "total_vulnerable": 2,
    "details": [
      {
        "file_path": "package.json",
        "vulnerable_dependencies": [
          {
            "name": "node-rsa",
            "current_version": "^1.1.1",
            "severity": "HIGH"
          }
        ]
      }
    ]
  }
}
```

### Config on fixture
Command used
- `python -` (script in terminal, repo root)

Sample output (excerpt)
```json
{
  "config": {
    "total_files_scanned": 1,
    "total_findings": 7,
    "details": [
      {
        "file_path": "nginx.conf",
        "findings": [
          {
            "type": "outdated_tls",
            "line": 1,
            "severity": "HIGH"
          },
          {
            "type": "rsa_cipher",
            "line": 2,
            "severity": "HIGH"
          }
        ]
      }
    ]
  }
}
```

## Output Contract Evaluation

### Raw scanner outputs
- Raw outputs are scanner-specific and do not include a unified schema (no `scanner_type`, `rule_id`, `line_end`, or consistent `message`).
- Example: SAST emits `type/line/code/algorithm`, SCA emits dependency fields, Config emits `type/line/matched_text`.

### Normalized findings (added)
- A unified schema is now produced and persisted in the `findings` table.
- Source: `backend/app/tasks.py:395`.
- Fields are stored in DB columns and `meta`: `scanner_type`, `rule_id`, `message`, `evidence`, `line_start/line_end`, and crypto fields where applicable.

Normalized sample (SAST)
```json
{
  "type": "rsa_keygen",
  "severity": "HIGH",
  "context": "SAST",
  "file_path": "VulnerableCrypto.java",
  "line_start": 10,
  "line_end": 10,
  "evidence": "KeyPairGenerator.getInstance(\"RSA\")",
  "meta": {
    "scanner_type": "SAST",
    "rule_id": "rsa_keygen",
    "message": "RSA KeyPairGenerator ...",
    "usage_type": "code",
    "recommendation": "..."
  }
}
```

Normalized sample (SCA)
```json
{
  "type": "node-rsa",
  "severity": "HIGH",
  "context": "SCA",
  "file_path": "package.json",
  "line_start": null,
  "line_end": null,
  "evidence": "node-rsa@^1.1.1",
  "meta": {
    "scanner_type": "SCA",
    "rule_id": "node-rsa",
    "message": "RSA-only library without PQC support.",
    "usage_type": "dependency",
    "library": "node-rsa",
    "current_version": "^1.1.1"
  }
}
```

Normalized sample (Config)
```json
{
  "type": "outdated_tls",
  "severity": "HIGH",
  "context": "CONFIG",
  "file_path": "nginx.conf",
  "line_start": 1,
  "line_end": 1,
  "evidence": "TLSv1.1",
  "meta": {
    "scanner_type": "CONFIG",
    "rule_id": "outdated_tls",
    "message": "Outdated TLS version",
    "usage_type": "config"
  }
}
```

## Issues Found (with file references)

### Critical
1. Scanner syntax errors prevented runtime imports (fixed)
- Broken string literals and docstrings in SAST/Config/SCA rule files.
- Examples: `3_scanner/scanners/sast/python_analyzer.py:41`, `3_scanner/scanners/sast/crypto_rules.py:42`, `3_scanner/scanners/sca/vulnerability_db.py:7`, `3_scanner/scanners/config/crypto_config_rules.py:49`.

2. Unicode emoji logging crashed on Windows console (fixed)
- `UnicodeEncodeError` occurred during scanning on cp949 terminals.
- Examples: `3_scanner/scanners/sast/scanner.py:66`, `3_scanner/scanners/sca/scanner.py:121`, `3_scanner/scanners/config/scanner.py:186`, `3_scanner/language_detector/repository_analyzer.py:22`.

### High
3. Dependency manifests were labeled as `unknown/json`, causing SCA to miss findings (fixed)
- Language override added for dependency files.
- Source: `3_scanner/language_detector/constants.py:117`, `3_scanner/language_detector/repository_analyzer.py:120`.

4. BOM in dependency manifests broke parsers (fixed)
- `package.json` and `requirements.txt` with BOM failed parsing.
- Source: `3_scanner/scanners/sca/parsers.py:19`, `3_scanner/scanners/sca/parsers.py:41`.

### Medium
5. Config results were not persisted or available to the AI layer (fixed)
- Now normalized and stored in `findings` alongside SAST and SCA.
- Source: `backend/app/tasks.py:95`, `backend/app/tasks.py:120`, `backend/app/tasks.py:395`.

6. Output contract was inconsistent across scanners (fixed via normalization)
- Unified normalization added to backend pipeline.
- Source: `backend/app/tasks.py:395`.

### Low
7. YAML structured scan TODO remains
- `3_scanner/scanners/config/scanner.py:107`.

8. Config target selection can miss crypto config outside keyword paths
- `3_scanner/language_detector/repository_analyzer.py:220`.

## Tests Added
- `3_scanner/tests/test_sast_scanner.py`
- `3_scanner/tests/test_sca_scanner.py`
- `3_scanner/tests/test_config_scanner.py`
- `backend/tests/test_findings_normalization.py`

Run
- `pytest 3_scanner/tests`
- `pytest backend/tests`

## Recommendations
1. Expand SCA vulnerability DB or connect to an advisory source for broader coverage.
2. Add structured YAML scanning and secret detection for config files.
3. Decide whether to expose normalized `findings` via API for AI consumption or consume directly from DB.
4. Add key-size extraction in SAST for RSA/ECC if needed for PQC readiness scoring.

## Verdict: AI-Ready?
Conditionally yes.
- After the fixes above, scanners execute, produce real findings, and normalized outputs are stored in `findings` with required fields for AI consumption.
- Remaining blockers are about coverage and enrichment, not basic correctness. If the AI model requires complete crypto asset context (key sizes, usage types, cert metadata), add those fields before model training.
