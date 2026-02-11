# scanners/config/crypto_config_rules.py

CONFIG_CRYPTO_PATTERNS = {
    # TLS version
    "outdated_tls": {
        "patterns": [
            r'TLSv1\.0',
            r'TLSv1\.1',
            r'ssl_protocols.*TLSv1\s',
        ],
        "severity": "HIGH",
        "description": "Outdated TLS protocol version (TLS 1.0/1.1).",
        "recommendation": "Upgrade to TLS 1.3."
    },
    
    # RSA cipher suites
    "rsa_cipher": {
        "patterns": [
            r'TLS_RSA_',
            r'ssl_ciphers.*RSA',
            r'RSA.*AES',
        ],
        "severity": "HIGH",
        "description": "RSA-based cipher suite usage.",
        "recommendation": "Migrate to PQC-safe cipher suites."
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
        "description": "ECC-based cipher suite usage.",
        "recommendation": "Migrate to PQC-safe cipher suites."
    },
    
    # DHE (Diffie-Hellman)
    "dhe_cipher": {
        "patterns": [
            r'TLS_DHE_',
            r'DHE-RSA',
        ],
        "severity": "MEDIUM",
        "description": "DHE 湲곕컲 ??援먰솚 ?ъ슜",
        "recommendation": "Consider PQC KEMs such as Kyber."
    },
    
    # Weak ciphers
    "weak_cipher": {
        "patterns": [
            r'DES',
            r'3DES',
            r'RC4',
            r'MD5',
        ],
        "severity": "CRITICAL",
        "description": "Weak cipher usage (DES/3DES/RC4/MD5).",
        "recommendation": "Remove immediately."
    }
}
