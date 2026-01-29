# scanners/sast/crypto_rules.py

# 취약한 암호화 패턴
CRYPTO_PATTERNS = {
    "python": {
        "rsa_generation": {
            "patterns": [
                r"RSA\.generate\s*\(\s*\d+\s*\)",
                r"rsa\.generate_private_key\s*\(",
            ],
            "severity": "HIGH",
            "algorithm": "RSA",
            "description": "RSA 키 생성 감지 - 양자컴퓨터에 취약",
            "recommendation": "Kyber(KEM) 또는 Dilithium(서명)으로 교체 권장"
        },
        "ecdsa_generation": {
            "patterns": [
                r"ec\.generate_private_key\s*\(",
                r"ECDSA\s*\(",
            ],
            "severity": "HIGH",
            "algorithm": "ECC/ECDSA",
            "description": "ECDSA 키 생성 감지 - 양자컴퓨터에 취약",
            "recommendation": "Dilithium 또는 Falcon으로 교체 권장"
        },
        "weak_hash": {
            "patterns": [
                r"hashlib\.(md5|sha1)\s*\(",
            ],
            "severity": "MEDIUM",
            "algorithm": "Weak Hash",
            "description": "약한 해시 함수 사용 (MD5/SHA1)",
            "recommendation": "SHA-256 이상 또는 SHA-3 사용 권장"
        },
        "rsa_import": {
            "patterns": [
                r"from\s+Crypto\.PublicKey\s+import\s+RSA",
                r"from\s+cryptography\.hazmat\.primitives\.asymmetric\s+import\s+rsa",
            ],
            "severity": "MEDIUM",
            "algorithm": "RSA",
            "description": "RSA 라이브러리 임포트",
            "recommendation": "PQC 라이브러리(pqcrypto, liboqs) 사용 검토"
        },
        "ecdsa_import": {
            "patterns": [
                r"from\s+cryptography\.hazmat\.primitives\.asymmetric\s+import\s+ec",
                r"import\s+ecdsa",
            ],
            "severity": "MEDIUM",
            "algorithm": "ECC",
            "description": "ECC/ECDSA 라이브러리 임포트",
            "recommendation": "PQC 서명 알고리즘 사용 검토"
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
            "description": "RSA 키 생성 감지",
            "recommendation": "PQC 라이브러리로 교체 권장"
        },
        "ecdsa_generation": {
            "patterns": [
                r"generateKeyPairSync\s*\(\s*['\"]ec['\"]",
                r"generateKeyPair\s*\(\s*['\"]ec['\"]",
            ],
            "severity": "HIGH",
            "algorithm": "ECC",
            "description": "ECC 키 생성 감지",
            "recommendation": "PQC 서명 알고리즘으로 교체 권장"
        },
        "crypto_require": {
            "patterns": [
                r"require\s*\(\s*['\"]crypto['\"]",
                r"require\s*\(\s*['\"]node-rsa['\"]",
            ],
            "severity": "MEDIUM",
            "algorithm": "RSA/ECC",
            "description": "암호화 라이브러리 사용",
            "recommendation": "사용 중인 알고리즘 확인 필요"
        }
    },
    
    "java": {
        "rsa_keygen": {
            "patterns": [
                r'KeyPairGenerator\.getInstance\s*\(\s*["\']RSA["\']\s*\)',
            ],
            "severity": "HIGH",
            "algorithm": "RSA",
            "description": "RSA KeyPairGenerator 사용",
            "recommendation": "PQC 알고리즘으로 교체 권장"
        },
        "ecdsa_keygen": {
            "patterns": [
                r'KeyPairGenerator\.getInstance\s*\(\s*["\']EC["\']\s*\)',
                r'Signature\.getInstance\s*\(\s*["\'].*ECDSA.*["\']\s*\)',
            ],
            "severity": "HIGH",
            "algorithm": "ECC",
            "description": "ECDSA 사용",
            "recommendation": "PQC 서명 알고리즘으로 교체 권장"
        }
    },
    
    "go": {
        "rsa_generation": {
            "patterns": [
                r"rsa\.GenerateKey\s*\(",
            ],
            "severity": "HIGH",
            "algorithm": "RSA",
            "description": "RSA 키 생성",
            "recommendation": "PQC 라이브러리 사용 권장"
        },
        "ecdsa_generation": {
            "patterns": [
                r"ecdsa\.GenerateKey\s*\(",
            ],
            "severity": "HIGH",
            "algorithm": "ECC",
            "description": "ECDSA 키 생성",
            "recommendation": "PQC 서명 알고리즘 사용 권장"
        }
    }
}

# 취약한 API 목록
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