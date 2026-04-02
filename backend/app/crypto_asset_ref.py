from __future__ import annotations


def canonical_algorithm_family(
    algorithm: str | None,
    *,
    rule_id: str | None = None,
    library: str | None = None,
    message: str | None = None,
) -> str:
    merged = " ".join(
        [
            str(algorithm or ""),
            str(rule_id or ""),
            str(library or ""),
            str(message or ""),
        ]
    ).lower()

    if "rsa" in merged or "rs256" in merged or "ps256" in merged:
        return "rsa-public-key"
    if any(token in merged for token in ("dh", "ecdh", "diffie")):
        return "dh-key-exchange"
    if any(token in merged for token in ("ecc", "ecdsa", "elliptic", "es256", "es384", "es512")):
        return "ecc-signature"
    if "dsa" in merged:
        return "dsa-signature"
    if any(token in merged for token in ("sha-1", "sha1", "md5", "weak hash")):
        return "weak-hash"
    return "legacy-crypto"


def infer_boundary_tag(file_path: str | None) -> str:
    path = str(file_path or "").lower()
    if any(token in path for token in ("auth", "login", "token", "jwt", "identity", "session")):
        return "auth-token"
    if any(token in path for token in ("tls", "ssl", "cert", "nginx", "gateway", "quic")):
        return "tls-cert"
    if "config" in path:
        return "config"
    if any(token in path for token in ("crypto", "security", "sign", "verify")):
        return "crypto-core"
    return "general"


def build_asset_ref(
    *,
    usage_type: str | None,
    algorithm_family: str,
    file_path: str | None,
    library: str | None = None,
) -> str:
    usage = str(usage_type or "unknown").lower()
    location = str(file_path or "repository").replace("\\", "/").lower()
    if library:
        return f"{usage}:{algorithm_family}:{location}#{str(library).lower()}"
    return f"{usage}:{algorithm_family}:{location}"


def build_correlation_ref(
    *,
    algorithm_family: str,
    file_path: str | None,
) -> str:
    boundary = infer_boundary_tag(file_path)
    return f"{algorithm_family}:{boundary}"
