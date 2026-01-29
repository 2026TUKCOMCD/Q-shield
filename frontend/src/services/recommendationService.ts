import { apiClient } from '../api'
import { handleError, type AppError } from '../utils/errorHandler'
import { logError } from '../utils/logger'

/**
 * 우선순위 타입
 */
export type Priority = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'

/**
 * 추천사항 타입
 */
export interface Recommendation {
  id: string
  priorityRank: number
  priority: Priority
  issueName: string
  estimatedEffort: string // e.g., "3 M/D"
  aiRecommendation: string // Markdown formatted
  recommendedPQCAlgorithm: string
  targetAlgorithm: string // 기존 알고리즘
  context: string // e.g., "payment logic", "authentication"
  filePath?: string // 파일 경로 (선택적)
}

/**
 * 추천사항 응답 타입
 */
export interface RecommendationsResponse {
  uuid: string
  recommendations: Recommendation[]
}

/**
 * 네트워크 지연 시뮬레이션 (0.5-1초)
 */
const simulateNetworkDelay = (): Promise<void> => {
  const delay = 500 + Math.random() * 500 // 0.5-1초
  return new Promise((resolve) => setTimeout(resolve, delay))
}

/**
 * 우선순위 랭크를 Priority로 변환
 */
const rankToPriority = (rank: number): Priority => {
  if (rank <= 2) return 'CRITICAL'
  if (rank <= 5) return 'HIGH'
  if (rank <= 8) return 'MEDIUM'
  return 'LOW'
}

/**
 * Mock 추천사항 데이터 생성
 */
const generateMockRecommendations = (uuid: string): Recommendation[] => {
  return [
    {
      id: 'rec-1',
      priorityRank: 1,
      priority: 'CRITICAL',
      issueName: 'Replace RSA-1024 with Kyber-768',
      estimatedEffort: '5 M/D',
      targetAlgorithm: 'RSA-1024',
      recommendedPQCAlgorithm: 'Kyber-768',
      context: 'authentication',
      filePath: 'src/auth.c',
      aiRecommendation: `## Why this is a risk

RSA-1024 is vulnerable to quantum attacks and will be broken by quantum computers. The National Institute of Standards and Technology (NIST) has deprecated RSA-1024 for new systems.

## Migration Guide

### Step 1: Replace Key Generation

\`\`\`c
// Before (RSA-1024)
RSA_generate_key(1024, RSA_F4, NULL, NULL);

// After (Kyber-768)
#include <oqs/oqs.h>
OQS_KEM *kem = OQS_KEM_new(OQS_KEM_alg_kyber_768);
uint8_t public_key[OQS_KEM_kyber_768_length_public_key];
uint8_t secret_key[OQS_KEM_kyber_768_length_secret_key];
OQS_KEM_keypair(kem, public_key, secret_key);
\`\`\`

### Step 2: Update Encryption/Decryption

Replace RSA encryption with Kyber encapsulation/decapsulation.

### Testing

- Verify key generation works correctly
- Test encryption/decryption flow
- Ensure backward compatibility during migration`,
    },
    {
      id: 'rec-2',
      priorityRank: 2,
      priority: 'CRITICAL',
      issueName: 'Replace SHA-1 with SHA-3',
      estimatedEffort: '3 M/D',
      targetAlgorithm: 'SHA-1',
      recommendedPQCAlgorithm: 'SHA-3-256',
      context: 'hashing',
      filePath: 'src/utils/hash.py',
      aiRecommendation: `## Why this is a risk

SHA-1 is cryptographically broken and vulnerable to collision attacks. It should be replaced with SHA-3, which is quantum-resistant.

## Migration Guide

### Step 1: Update Hash Function

\`\`\`python
# Before (SHA-1)
import hashlib
hash = hashlib.sha1(data).hexdigest()

# After (SHA-3-256)
import hashlib
hash = hashlib.sha3_256(data).hexdigest()
\`\`\`

### Step 2: Update All References

Search for all SHA-1 usages and replace with SHA-3-256.

### Testing

- Verify hash outputs are correct
- Update any stored hash values
- Test hash verification logic`,
    },
    {
      id: 'rec-3',
      priorityRank: 3,
      priority: 'HIGH',
      issueName: 'Replace AES-128 with AES-256',
      estimatedEffort: '2 M/D',
      targetAlgorithm: 'AES-128',
      recommendedPQCAlgorithm: 'AES-256',
      context: 'encryption',
      filePath: 'config/settings.json',
      aiRecommendation: `## Why this is a risk

While AES-128 is still secure, AES-256 provides better security margins against future quantum attacks and follows NIST recommendations.

## Migration Guide

### Step 1: Update Key Size

\`\`\`javascript
// Before (AES-128)
const key = crypto.randomBytes(16); // 128 bits

// After (AES-256)
const key = crypto.randomBytes(32); // 256 bits
\`\`\`

### Step 2: Update Cipher Configuration

Ensure all AES operations use 256-bit keys.

### Testing

- Verify encryption/decryption works
- Test key generation
- Ensure performance is acceptable`,
    },
    {
      id: 'rec-4',
      priorityRank: 4,
      priority: 'HIGH',
      issueName: 'Replace ECDSA with Dilithium',
      estimatedEffort: '4 M/D',
      targetAlgorithm: 'ECDSA',
      recommendedPQCAlgorithm: 'Dilithium-3',
      context: 'digital signatures',
      filePath: 'src/crypto/signature.c',
      aiRecommendation: `## Why this is a risk

ECDSA (Elliptic Curve Digital Signature Algorithm) is vulnerable to quantum attacks. Dilithium is a post-quantum signature scheme selected by NIST.

## Migration Guide

### Step 1: Replace Signature Generation

\`\`\`c
// Before (ECDSA)
ECDSA_SIG *sig = ECDSA_do_sign(hash, hash_len, eckey);

// After (Dilithium-3)
#include <oqs/oqs.h>
OQS_SIG *sig = OQS_SIG_new(OQS_SIG_alg_dilithium_3);
uint8_t signature[OQS_SIG_dilithium_3_length_signature];
OQS_SIG_sign(sig, signature, &sig_len, message, message_len, secret_key);
\`\`\`

### Step 2: Update Verification

Replace ECDSA verification with Dilithium verification.

### Testing

- Test signature generation
- Verify signature validation
- Ensure compatibility with existing systems`,
    },
    {
      id: 'rec-5',
      priorityRank: 5,
      priority: 'HIGH',
      issueName: 'Replace RSA-2048 with CRYSTALS-Kyber',
      estimatedEffort: '6 M/D',
      targetAlgorithm: 'RSA-2048',
      recommendedPQCAlgorithm: 'CRYSTALS-Kyber-1024',
      context: 'key exchange',
      filePath: 'src/network/tls.c',
      aiRecommendation: `## Why this is a risk

RSA-2048 will be vulnerable to quantum attacks. CRYSTALS-Kyber is a post-quantum key encapsulation mechanism standardized by NIST.

## Migration Guide

### Step 1: Update TLS Configuration

\`\`\`c
// Before (RSA-2048)
SSL_CTX_set_cipher_list(ctx, "RSA-AES256-GCM-SHA384");

// After (CRYSTALS-Kyber)
SSL_CTX_set_cipher_list(ctx, "KYBER-AES256-GCM-SHA384");
\`\`\`

### Step 2: Update Key Exchange Logic

Replace RSA key exchange with Kyber key encapsulation.

### Testing

- Test TLS handshake
- Verify key exchange works
- Ensure backward compatibility`,
    },
    {
      id: 'rec-6',
      priorityRank: 6,
      priority: 'MEDIUM',
      issueName: 'Replace MD5 with SHA-3',
      estimatedEffort: '1 M/D',
      targetAlgorithm: 'MD5',
      recommendedPQCAlgorithm: 'SHA-3-256',
      context: 'checksum',
      filePath: 'src/utils/checksum.c',
      aiRecommendation: `## Why this is a risk

MD5 is cryptographically broken and should never be used for security purposes. SHA-3 provides quantum resistance.

## Migration Guide

### Step 1: Replace Hash Function

\`\`\`c
// Before (MD5)
MD5_Init(&ctx);
MD5_Update(&ctx, data, len);
MD5_Final(digest, &ctx);

// After (SHA-3-256)
#include <oqs/oqs.h>
OQS_HASH *hash = OQS_HASH_new(OQS_HASH_alg_sha3_256);
uint8_t digest[OQS_HASH_sha3_256_length_digest];
OQS_HASH(hash, digest, data, len);
\`\`\`

### Testing

- Verify hash outputs
- Update stored checksums
- Test verification logic`,
    },
  ]
}

/**
 * 추천사항 서비스
 */
export const recommendationService = {
  /**
   * 스캔 추천사항 조회
   * Mock: 요구사항에 맞는 더미 데이터 반환
   */
  async getRecommendations(
    uuid: string,
    filters?: {
      algorithmType?: string
      context?: string
      priority?: Priority
    }
  ): Promise<RecommendationsResponse> {
    try {
      // 네트워크 지연 시뮬레이션
      await simulateNetworkDelay()

      // 실제 API 호출 (현재는 mock)
      // const params = new URLSearchParams()
      // if (filters?.algorithmType) params.append('algorithmType', filters.algorithmType)
      // if (filters?.context) params.append('context', filters.context)
      // const response = await apiClient.get<RecommendationsResponse>(
      //   `/scans/${uuid}/recommendations?${params.toString()}`
      // )
      // return response.data

      // localStorage에서 캐시 확인
      const recommendationKey = `pqc-scanner-recommendations-${uuid}`
      const cached = localStorage.getItem(recommendationKey)
      let recommendations: Recommendation[] = []

      if (cached) {
        const cachedData = JSON.parse(cached) as RecommendationsResponse
        recommendations = cachedData.recommendations
      } else {
        // Mock 데이터 생성
        recommendations = generateMockRecommendations(uuid)
        const mockResponse: RecommendationsResponse = {
          uuid,
          recommendations,
        }
        localStorage.setItem(recommendationKey, JSON.stringify(mockResponse))
      }

      // 필터링 적용
      let filtered = recommendations

      if (filters?.algorithmType) {
        filtered = filtered.filter(
          (rec) =>
            rec.targetAlgorithm.toLowerCase().includes(filters.algorithmType!.toLowerCase()) ||
            rec.recommendedPQCAlgorithm.toLowerCase().includes(filters.algorithmType!.toLowerCase())
        )
      }

      if (filters?.context) {
        filtered = filtered.filter((rec) =>
          rec.context.toLowerCase().includes(filters.context!.toLowerCase())
        )
      }

      if (filters?.priority) {
        filtered = filtered.filter((rec) => rec.priority === filters.priority)
      }

      return {
        uuid,
        recommendations: filtered,
      }
    } catch (error) {
      logError('Failed to get recommendations', error)
      throw handleError(error) as AppError
    }
  },
}
