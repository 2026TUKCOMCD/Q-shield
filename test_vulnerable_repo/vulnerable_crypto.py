# Python - RSA 취약점
from Crypto.PublicKey import RSA
from cryptography.hazmat.primitives.asymmetric import rsa
import hashlib

# 취약점 1: RSA 키 생성
def generate_rsa_key():
    key = RSA.generate(2048)
    return key

# 취약점 2: cryptography 라이브러리로 RSA 생성
def generate_rsa_key_v2():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    return private_key

# 취약점 3: 약한 해시 함수
def weak_hash(data):
    return hashlib.md5(data).hexdigest()

# 취약점 4: SHA1 해시
def weak_hash_sha1(data):
    return hashlib.sha1(data).hexdigest()
