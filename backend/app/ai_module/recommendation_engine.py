from __future__ import annotations

from collections import Counter

from app.ai_module.rag import retrieve_citations
from app.ai_module.schemas import RecommendationPayload


RECOMMENDATION_RULES = {
    "rsa": {
        "title": "Replace RSA key establishment with ML-KEM (Kyber)",
        "description": "RSA usage indicates a quantum-vulnerable key establishment path. Migrate key exchange and encapsulation to ML-KEM compatible libraries such as liboqs-backed implementations.",
        "nist_standard_reference": "FIPS 203 (ML-KEM)",
        "query": "ml-kem kyber rsa migration key establishment fips 203",
    },
    "dh": {
        "title": "Replace DH/ECDH style key exchange with ML-KEM (Kyber)",
        "description": "Diffie-Hellman style key exchange appears in the scan data. Replace quantum-vulnerable exchange paths with ML-KEM and update protocol negotiation accordingly.",
        "nist_standard_reference": "FIPS 203 (ML-KEM)",
        "query": "ml-kem kyber dh ecdh migration fips 203",
    },
    "ecc": {
        "title": "Replace ECC signatures with ML-DSA (Dilithium)",
        "description": "ECC or ECDSA signatures are present. Plan a phased move to ML-DSA for signature generation and verification, with hybrid support where interoperability is required.",
        "nist_standard_reference": "FIPS 204 (ML-DSA)",
        "query": "ml-dsa dilithium ecc ecdsa migration fips 204",
    },
    "dsa": {
        "title": "Replace DSA signatures with ML-DSA (Dilithium)",
        "description": "DSA-based signatures are quantum-vulnerable. Replace signing operations and key management with ML-DSA-capable libraries.",
        "nist_standard_reference": "FIPS 204 (ML-DSA)",
        "query": "ml-dsa dilithium dsa migration fips 204",
    },
    "sha-1": {
        "title": "Remove SHA-1 and align with NIST transition guidance",
        "description": "SHA-1 or MD5 usage signals legacy cryptography debt. Eliminate weak hashes first, then align dependent workflows with PQC migration for signatures and key exchange.",
        "nist_standard_reference": "SP 800-131A Rev. 2",
        "query": "nist sp 800-131a sha-1 transition weak hash",
    },
    "library": {
        "title": "Replace legacy crypto libraries with PQC-capable libraries",
        "description": "The dependency graph contains libraries without PQC support. Prioritize liboqs or vendor-supported PQC integrations for shared crypto abstractions.",
        "nist_standard_reference": "SP 1800-38B (Preliminary Draft)",
        "query": "liboqs migration pqc library transition",
    },
}


def _match_rule_key(finding: dict) -> str:
    algorithm = str(finding.get("algorithm") or "").lower()
    meta = finding.get("meta") or {}
    library = str(meta.get("library") or "").lower()

    if "rsa" in algorithm or "rsa" in library:
        return "rsa"
    if any(token in algorithm for token in ("dh", "diffie")) or any(token in library for token in ("dh", "diffie")):
        return "dh"
    if any(token in algorithm for token in ("ecc", "ecdsa")) or any(token in library for token in ("ecc", "ecdsa", "elliptic")):
        return "ecc"
    if "dsa" in algorithm or "dsa" in library:
        return "dsa"
    if any(token in algorithm for token in ("sha-1", "sha1", "md5")) or any(token in library for token in ("sha-1", "sha1", "md5")):
        return "sha-1"
    if meta.get("usage_type") == "dependency":
        return "library"
    return "library"


def build_recommendations(
    findings: list[dict],
    *,
    top_k: int = 3,
    corpus_path: str | None = None,
) -> tuple[list[RecommendationPayload], list[dict], bool, list[str]]:
    if not findings:
        return [], [], True, []

    rule_counter: Counter[str] = Counter(_match_rule_key(finding) for finding in findings)
    recommendations: list[RecommendationPayload] = []
    all_citations: list[dict] = []
    nist_references: list[str] = []

    for rule_key, _ in rule_counter.most_common(top_k):
        template = RECOMMENDATION_RULES[rule_key]
        citations = retrieve_citations(template["query"], top_k=2, corpus_path=corpus_path)
        citation_models = [citation for citation in citations]
        all_citations.extend(citation.model_dump() for citation in citation_models)
        nist_reference = template["nist_standard_reference"] if citation_models else "N/A"
        nist_references.append(nist_reference)

        base_confidence = 0.65 if citation_models else 0.45
        recommendations.append(
            RecommendationPayload(
                title=template["title"],
                description=template["description"],
                nist_standard_reference=nist_reference,
                citations=citation_models,
                confidence=round(min(1.0, base_confidence + (0.05 * len(citation_models))), 4),
            )
        )

    citation_missing = not all_citations
    deduped_references = [reference for reference in dict.fromkeys(nist_references) if reference]
    return recommendations, all_citations, citation_missing, deduped_references
