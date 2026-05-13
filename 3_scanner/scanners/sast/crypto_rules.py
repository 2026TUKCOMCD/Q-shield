# scanners/sast/crypto_rules.py

# Cryptographic patterns for vulnerable usage
CRYPTO_PATTERNS = {
    "python": {
        "rsa_generation": {
            "patterns": [
                r"RSA\.generate\s*\(\s*\d+\s*\)",
                r"rsa\.generate_private_key\s*\(",
            ],
            "severity": "HIGH",
            "algorithm": "RSA",
            "description": "RSA key generation detected - vulnerable to quantum attacks.",
            "recommendation": "Consider Kyber (KEM) or Dilithium (signatures)."
        },
        "ecdsa_generation": {
            "patterns": [
                r"ec\.generate_private_key\s*\(",
                r"ECDSA\s*\(",
            ],
            "severity": "HIGH",
            "algorithm": "ECC/ECDSA",
            "description": "ECDSA key generation detected - vulnerable to quantum attacks.",
            "recommendation": "Consider Dilithium or Falcon."
        },
        "weak_hash": {
            "patterns": [
                r"hashlib\.(md5|sha1)\s*\(",
            ],
            "severity": "MEDIUM",
            "algorithm": "Weak Hash",
            "description": "Weak hash function usage (MD5/SHA1).",
            "recommendation": "Use SHA-256 or SHA-3."
        },
        "rsa_import": {
            "patterns": [
                r"from\s+Crypto\.PublicKey\s+import\s+RSA",
                r"from\s+cryptography\.hazmat\.primitives\.asymmetric\s+import\s+rsa",
            ],
            "severity": "MEDIUM",
            "algorithm": "RSA",
            "description": "RSA library import detected.",
            "recommendation": "Consider PQC-safe libraries (pqcrypto, liboqs)."
        },
        "ecdsa_import": {
            "patterns": [
                r"from\s+cryptography\.hazmat\.primitives\.asymmetric\s+import\s+ec",
                r"import\s+ecdsa",
            ],
            "severity": "MEDIUM",
            "algorithm": "ECC",
            "description": "ECC/ECDSA library import detected.",
            "recommendation": "Consider PQC signature algorithms."
        },
        "jwt_library_usage": {
            "patterns": [
                r"^\s*import\s+jwt\b",
                r"^\s*from\s+jose\s+import\s+jwt\b",
                r"^\s*from\s+jose\s+import\s+jws\b",
                r"^\s*import\s+authlib\.jose\b",
                r"^\s*from\s+authlib\.jose\s+import\s+JsonWeb(Signature|Token)\b",
            ],
            "severity": "MEDIUM",
            "algorithm": "JWT/JOSE",
            "description": "JWT/JOSE library usage detected. Verify whether RSA or ECDSA signing is used.",
            "recommendation": "Inspect signing algorithms and plan migration away from RSA/ECDSA-based JWT signatures."
        },
        "jwt_rsa_algorithm": {
            "patterns": [
                r"algorithm\s*=\s*['\"](RS256|RS384|RS512|PS256|PS384|PS512)['\"]",
                r"algorithms\s*=\s*\[[^\]]*['\"](RS256|RS384|RS512|PS256|PS384|PS512)['\"]",
            ],
            "severity": "HIGH",
            "algorithm": "RSA",
            "description": "RSA-based JWT/JOSE signing algorithm detected.",
            "recommendation": "Plan migration away from RSA/RSASSA-PSS signatures and introduce PQC-ready signing architecture."
        },
        "jwt_ecdsa_algorithm": {
            "patterns": [
                r"algorithm\s*=\s*['\"](ES256|ES384|ES512)['\"]",
                r"algorithms\s*=\s*\[[^\]]*['\"](ES256|ES384|ES512)['\"]",
            ],
            "severity": "HIGH",
            "algorithm": "ECC/ECDSA",
            "description": "ECDSA-based JWT/JOSE signing algorithm detected.",
            "recommendation": "Plan migration away from ECDSA signatures and introduce PQC-ready signing architecture."
        },
        "dh_keygen": {
            "patterns": [
                r"generate_parameters\s*\(.*key_size\s*=",
                r"from\s+cryptography\.hazmat\.primitives\.asymmetric\.dh\s+import",
                r"dh\.generate_parameters\s*\(",
            ],
            "severity": "HIGH",
            "algorithm": "DH",
            "description": "Diffie-Hellman key exchange detected - Shor-breakable.",
            "recommendation": "Replace with ML-KEM (FIPS 203)."
        }
    },

    "javascript": {
        "rsa_generation": {
            "patterns": [
                r"generateKeyPairSync\s*\(\s*['\"]rsa['\"]",
                r"generateKeyPair\s*\(\s*['\"]rsa['\"]",
            ],
            "severity": "HIGH",
            "algorithm": "RSA",
            "description": "RSA key generation detected.",
            "recommendation": "Consider PQC-safe libraries."
        },
        "ecdsa_generation": {
            "patterns": [
                r"generateKeyPairSync\s*\(\s*['\"]ec['\"]",
                r"generateKeyPair\s*\(\s*['\"]ec['\"]",
            ],
            "severity": "HIGH",
            "algorithm": "ECC",
            "description": "ECC key generation detected.",
            "recommendation": "Consider PQC signature algorithms."
        },
        "crypto_require": {
            "patterns": [
                r"require\s*\(\s*['\"]crypto['\"]",
                r"require\s*\(\s*['\"]node-rsa['\"]",
            ],
            "severity": "MEDIUM",
            "algorithm": "RSA/ECC",
            "description": "Cryptographic library usage detected.",
            "recommendation": "Verify algorithm usage and migrate if needed."
        },
        "jwt_library_usage": {
            "patterns": [
                r"require\s*\(\s*['\"]jsonwebtoken['\"]",
                r"require\s*\(\s*['\"]jose['\"]",
                r"require\s*\(\s*['\"]node-jose['\"]",
                r"import\s+.*from\s+['\"]jsonwebtoken['\"]",
                r"import\s+.*from\s+['\"]jose['\"]",
                r"import\s+.*from\s+['\"]node-jose['\"]",
            ],
            "severity": "MEDIUM",
            "algorithm": "JWT/JOSE",
            "description": "JWT/JOSE library usage detected. Verify whether RSA or ECDSA signing is used.",
            "recommendation": "Inspect signing algorithms and migrate away from RSA/ECDSA-based JWT signatures."
        },
        "jwt_rsa_algorithm": {
            "patterns": [
                r"algorithm\s*:\s*['\"](RS256|RS384|RS512|PS256|PS384|PS512)['\"]",
                r"createSign\s*\(\s*['\"]RSA-[A-Z0-9-]+['\"]",
            ],
            "severity": "HIGH",
            "algorithm": "RSA",
            "description": "RSA-based JWT/JOSE signing algorithm detected.",
            "recommendation": "Plan migration away from RSA/RSASSA-PSS signatures and introduce PQC-ready signing architecture."
        },
        "jwt_ecdsa_algorithm": {
            "patterns": [
                r"algorithm\s*:\s*['\"](ES256|ES384|ES512)['\"]",
                r"createSign\s*\(\s*['\"]ecdsa-with-SHA\d+['\"]",
            ],
            "severity": "HIGH",
            "algorithm": "ECC/ECDSA",
            "description": "ECDSA-based JWT/JOSE signing algorithm detected.",
            "recommendation": "Plan migration away from ECDSA signatures and introduce PQC-ready signing architecture."
        }
    },
    
    "java": {
        "rsa_keygen": {
            "patterns": [
                r'KeyPairGenerator\.getInstance\s*\(\s*["\']RSA["\']\s*\)',
            ],
            "severity": "HIGH",
            "algorithm": "RSA",
            "description": "RSA KeyPairGenerator usage detected.",
            "recommendation": "Consider PQC key exchange/signature algorithms."
        },
        "ecdsa_keygen": {
            "patterns": [
                r'KeyPairGenerator\.getInstance\s*\(\s*["\']EC["\']\s*\)',
                r'Signature\.getInstance\s*\(\s*["\'].*ECDSA.*["\']\s*\)',
            ],
            "severity": "HIGH",
            "algorithm": "ECC",
            "description": "ECDSA usage detected.",
            "recommendation": "Consider PQC signature algorithms."
        },
        "rsa_signature": {
            "patterns": [
                r'Signature\.getInstance\s*\(\s*["\'].*RSA.*["\']\s*\)',
                r'Cipher\.getInstance\s*\(\s*["\']RSA\/',
            ],
            "severity": "HIGH",
            "algorithm": "RSA",
            "description": "RSA signature or cipher usage detected.",
            "recommendation": "Plan migration away from RSA-based signing and encryption flows."
        },
        "jwt_library_usage": {
            "patterns": [
                r'^\s*import\s+io\.jsonwebtoken\.',
                r'^\s*import\s+com\.nimbusds\.jose\.',
                r'^\s*import\s+org\.jose4j\.',
            ],
            "severity": "MEDIUM",
            "algorithm": "JWT/JOSE",
            "description": "JWT/JOSE library usage detected. Verify whether RSA or ECDSA signing is used.",
            "recommendation": "Inspect signing algorithms and migrate away from RSA/ECDSA-based JWT signatures."
        },
        "jwt_rsa_algorithm": {
            "patterns": [
                r'JWSAlgorithm\.(RS256|RS384|RS512|PS256|PS384|PS512)\b',
                r'SignatureAlgorithm\.(RS256|RS384|RS512|PS256|PS384|PS512)\b',
            ],
            "severity": "HIGH",
            "algorithm": "RSA",
            "description": "RSA-based JWT/JOSE signing algorithm detected.",
            "recommendation": "Plan migration away from RSA/RSASSA-PSS signatures and introduce PQC-ready signing architecture."
        },
        "jwt_ecdsa_algorithm": {
            "patterns": [
                r'JWSAlgorithm\.(ES256|ES384|ES512)\b',
                r'SignatureAlgorithm\.(ES256|ES384|ES512)\b',
            ],
            "severity": "HIGH",
            "algorithm": "ECC/ECDSA",
            "description": "ECDSA-based JWT/JOSE signing algorithm detected.",
            "recommendation": "Plan migration away from ECDSA signatures and introduce PQC-ready signing architecture."
        },
        "rsa_key_factory": {
            "patterns": [
                r'KeyFactory\.getInstance\s*\(\s*["\']RSA["\']\s*\)',
            ],
            "severity": "HIGH",
            "algorithm": "RSA",
            "description": "RSA KeyFactory usage detected - constructs RSA keys from raw material.",
            "recommendation": "Replace with ML-KEM (FIPS 203) key encapsulation."
        },
        "dsa_keygen": {
            "patterns": [
                r'KeyPairGenerator\.getInstance\s*\(\s*["\']DSA["\']\s*\)',
                r'Signature\.getInstance\s*\(\s*["\'].*DSA.*["\']\s*\)',
            ],
            "severity": "HIGH",
            "algorithm": "DSA",
            "description": "DSA key generation or signature detected - Shor-breakable.",
            "recommendation": "Replace with ML-DSA (FIPS 204)."
        },
        "dh_keygen": {
            "patterns": [
                r'KeyPairGenerator\.getInstance\s*\(\s*["\']DH["\']\s*\)',
                r'KeyAgreement\.getInstance\s*\(\s*["\']DH["\']\s*\)',
            ],
            "severity": "HIGH",
            "algorithm": "DH",
            "description": "Diffie-Hellman key exchange detected - Shor-breakable.",
            "recommendation": "Replace with ML-KEM (FIPS 203)."
        },
        "ecc_curve25519": {
            "patterns": [
                r'KeyPairGenerator\.getInstance\s*\(\s*["\']Ed25519["\']\s*\)',
                r'KeyPairGenerator\.getInstance\s*\(\s*["\']X25519["\']\s*\)',
                r'KeyPairGenerator\.getInstance\s*\(\s*["\']Ed448["\']\s*\)',
            ],
            "severity": "HIGH",
            "algorithm": "ECC/Ed25519",
            "description": "Curve25519/Ed25519 usage detected - Shor-breakable elliptic curve.",
            "recommendation": "Replace with ML-DSA (FIPS 204) for signatures."
        },
        "weak_hash_java": {
            "patterns": [
                r'MessageDigest\.getInstance\s*\(\s*["\']MD5["\']\s*\)',
                r'MessageDigest\.getInstance\s*\(\s*["\']SHA-1["\']\s*\)',
                r'MessageDigest\.getInstance\s*\(\s*["\']SHA1["\']\s*\)',
            ],
            "severity": "MEDIUM",
            "algorithm": "MD5/SHA-1",
            "description": "Weak hash function (MD5/SHA-1) detected - Grover-weakened.",
            "recommendation": "Replace with SHA-3 or SHA-256 (minimum)."
        },
        "weak_symmetric_java": {
            "patterns": [
                r'KeyGenerator\.getInstance\s*\(\s*["\']DESede["\']\s*\)',
                r'KeyGenerator\.getInstance\s*\(\s*["\']DES["\']\s*\)',
                r'Cipher\.getInstance\s*\(\s*["\']DESede',
                r'Cipher\.getInstance\s*\(\s*["\']DES/',
            ],
            "severity": "HIGH",
            "algorithm": "3DES/DES",
            "description": "3DES/DES symmetric cipher detected - critically weakened by Grover.",
            "recommendation": "Replace with AES-256-GCM."
        },
        "hardcoded_key": {
            "patterns": [
                r'new\s+SecretKeySpec\s*\(\s*["\'][^"\']{8,}["\']\s*\.getBytes',
                r'private\s+static\s+final\s+byte\[\]\s+\w*[Kk][Ee][Yy]\w*\s*=',
                r'private\s+static\s+final\s+String\s+\w*[Kk][Ee][Yy]\w*\s*=\s*["\']',
            ],
            "severity": "HIGH",
            "algorithm": "HARDCODED_KEY",
            "description": "Hardcoded cryptographic key material detected.",
            "recommendation": "Use a key management system (KMS). Never hardcode key material."
        }
    },
    
    "go": {
        "rsa_generation": {
            "patterns": [
                r"rsa\.GenerateKey\s*\(",
            ],
            "severity": "HIGH",
            "algorithm": "RSA",
            "description": "RSA key generation detected.",
            "recommendation": "Consider PQC-safe libraries."
        },
        "ecdsa_generation": {
            "patterns": [
                r"ecdsa\.GenerateKey\s*\(",
            ],
            "severity": "HIGH",
            "algorithm": "ECC",
            "description": "ECDSA key generation detected.",
            "recommendation": "Consider PQC signature algorithms."
        }
    }
}

# Vulnerable crypto API list
VULNERABLE_APIS = {
    "python": [
        "Crypto.PublicKey.RSA",
        "cryptography.hazmat.primitives.asymmetric.rsa",
        "cryptography.hazmat.primitives.asymmetric.ec",
        "ecdsa",
        "M2Crypto.RSA",
        "jwt",
        "jose.jwt",
        "jose.jws",
        "authlib.jose",
    ],
    "javascript": [
        "crypto.generateKeyPairSync",
        "crypto.createSign",
        "node-rsa",
        "jsrsasign",
        "jsonwebtoken",
        "jose",
        "node-jose",
    ],
    "java": [
        "java.security.KeyPairGenerator",
        "javax.crypto.Cipher",
        "io.jsonwebtoken",
        "com.nimbusds.jose",
        "org.jose4j",
    ],
    "go": [
        "crypto/rsa",
        "crypto/ecdsa",
    ]
}
