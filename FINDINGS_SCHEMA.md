# Findings Schema (Normalized)

Scope: normalized findings persisted to the DB via `backend/app/models.py` (`Finding`) and produced by normalization in `backend/app/tasks.py`.

**Required top-level fields (DB columns)**
- `type`: string (<= 20 chars). Stable rule identifier for the scanner.
- `severity`: string enum. One of `CRITICAL|HIGH|MEDIUM|LOW|INFO`.
- `algorithm`: string or null.
- `context`: string or null. Used for `scanner_type` (e.g., `SAST`, `SCA`, `CONFIG`).
- `file_path`: string or null. Path relative to repo root.
- `line_start`: int or null.
- `line_end`: int or null.
- `evidence`: string or null.
- `meta`: object (JSON). Must include the required keys below.

**Required meta fields**
- `scanner_type`: string. `SAST|SCA|CONFIG`.
- `rule_id`: string. Stable identifier for the rule/library/config rule.
- `message`: string. Human-readable summary.
- `severity_score`: int. Numeric score derived from severity mapping.
- `usage_type`: string. One of `code|dependency|config`.

**Optional meta fields**
- SAST: `detected_pattern`, `recommendation`.
- SCA: `library`, `current_version`, `dependency_type`, `pqc_support`, `pqc_version`, `alternatives`.
- CONFIG: `recommendation`, `duplicate_count` (added during dedup).

## Examples

**SAST**
```json
{
  "type": "rsa_generation",
  "severity": "HIGH",
  "algorithm": "RSA",
  "context": "SAST",
  "file_path": "src/app.py",
  "line_start": 10,
  "line_end": 10,
  "evidence": "RSA.generate(2048)",
  "meta": {
    "scanner_type": "SAST",
    "rule_id": "rsa_generation",
    "message": "RSA key generation detected",
    "severity_score": 80,
    "usage_type": "code",
    "detected_pattern": "RSA.generate",
    "recommendation": "Use PQC-safe alternatives"
  }
}
```

**SCA**
```json
{
  "type": "node-rsa",
  "severity": "HIGH",
  "algorithm": null,
  "context": "SCA",
  "file_path": "package.json",
  "line_start": null,
  "line_end": null,
  "evidence": "node-rsa@1.1.1",
  "meta": {
    "scanner_type": "SCA",
    "rule_id": "node-rsa",
    "message": "RSA-only library without PQC support.",
    "severity_score": 80,
    "usage_type": "dependency",
    "library": "node-rsa",
    "current_version": "1.1.1",
    "dependency_type": "runtime",
    "pqc_support": false,
    "alternatives": []
  }
}
```

**CONFIG**
```json
{
  "type": "outdated_tls",
  "severity": "HIGH",
  "algorithm": null,
  "context": "CONFIG",
  "file_path": "nginx.conf",
  "line_start": 1,
  "line_end": 1,
  "evidence": "TLSv1.0",
  "meta": {
    "scanner_type": "CONFIG",
    "rule_id": "outdated_tls",
    "message": "Outdated TLS version",
    "severity_score": 80,
    "usage_type": "config",
    "recommendation": "Upgrade to TLS 1.3"
  }
}
```
