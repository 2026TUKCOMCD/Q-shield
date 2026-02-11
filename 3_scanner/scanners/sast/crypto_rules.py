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
    ],
    "javascript": [
        "crypto.generateKeyPairSync",
        "crypto.createSign",
        "node-rsa",
        "jsrsasign",
    ],
    "java": [
        "java.security.KeyPairGenerator",
        "javax.crypto.Cipher",
    ],
    "go": [
        "crypto/rsa",
        "crypto/ecdsa",
    ]
}
