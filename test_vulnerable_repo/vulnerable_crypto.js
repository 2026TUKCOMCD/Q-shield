// JavaScript - RSA/ECC 취약점
const crypto = require('crypto');

// 취약점 1: RSA 키 생성
function generateRSAKey() {
    const { publicKey, privateKey } = crypto.generateKeyPairSync('rsa', {
        modulusLength: 2048,
    });
    return { publicKey, privateKey };
}

// 취약점 2: ECC 키 생성
function generateECKey() {
    const { publicKey, privateKey } = crypto.generateKeyPairSync('ec', {
        namedCurve: 'prime256v1',
    });
    return { publicKey, privateKey };
}

// 취약점 3: node-rsa 사용
const NodeRSA = require('node-rsa');

function encryptWithNodeRSA(data) {
    const key = new NodeRSA({ b: 2048 });
    return key.encrypt(data);
}
