# scanners/config/crypto_config_rules.py

CONFIG_CRYPTO_PATTERNS = {
    # TLS 버전
    "outdated_tls": {
        "patterns": [
            r'TLSv1\.0',
            r'TLSv1\.1',
            r'ssl_protocols.*TLSv1\s',
        ],
        "severity": "HIGH",
        "description": "구버전 TLS 프로토콜 사용 (TLS 1.0/1.1)",
        "recommendation": "TLS 1.3으로 업그레이드 필요"
    },
    
    # RSA 암호화 스위트
    "rsa_cipher": {
        "patterns": [
            r'TLS_RSA_',
            r'ssl_ciphers.*RSA',
            r'RSA.*AES',
        ],
        "severity": "HIGH",
        "description": "RSA 기반 암호화 스위트 사용",
        "recommendation": "PQC 안전 암호화 스위트로 교체 필요"
    },
    
    # ECDSA/ECDHE
    "ecdsa_cipher": {
        "patterns": [
            r'TLS_ECDSA_',
            r'TLS_ECDHE_',
            r'ECDHE-RSA',
            r'ECDHE-ECDSA',
        ],
        "severity": "HIGH",
        "description": "ECC 기반 암호화 스위트 사용",
        "recommendation": "PQC 안전 암호화 스위트로 교체 필요"
    },
    
    # DHE (Diffie-Hellman)
    "dhe_cipher": {
        "patterns": [
            r'TLS_DHE_',
            r'DHE-RSA',
        ],
        "severity": "MEDIUM",
        "description": "DHE 기반 키 교환 사용",
        "recommendation": "PQC KEM(예: Kyber) 사용 검토"
    },
    
    # 약한 암호화
    "weak_cipher": {
        "patterns": [
            r'DES',
            r'3DES',
            r'RC4',
            r'MD5',
        ],
        "severity": "CRITICAL",
        "description": "약한 암호화 알고리즘 사용",
        "recommendation": "즉시 제거 필요"
    }
}