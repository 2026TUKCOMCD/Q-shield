import { apiClient } from '../api'
import { handleError, type AppError } from '../utils/errorHandler'
import { logError } from '../utils/logger'

/**
 * 암호화 자산 타입
 */
export interface CryptographicAsset {
  id: string
  algorithmType: string
  filePath: string
  lineNumbers: number[]
  riskScore: number
}

/**
 * 암호화 자산 상세 정보 타입
 */
export interface AssetDetail extends CryptographicAsset {
  // Technical Specifications
  keySize?: number // 비트 단위
  modeOfOperation?: string // e.g., "CBC", "GCM", "ECB"
  implementation?: string // e.g., "OpenSSL", "BouncyCastle"
  standard?: string // e.g., "NIST FIPS 186-4", "RFC 3447"
  keyDerivationFunction?: string
  paddingScheme?: string // e.g., "PKCS#1 v1.5", "OAEP"
  
  // Context & Location
  codeSnippet?: string // 감지된 코드 스니펫
  detectedPattern?: string // 감지된 패턴 설명
  
  // AI Recommendations
  suggestedPQCAlternatives?: string[] // 추천 PQC 알고리즘 목록
  migrationComplexity?: 'Low' | 'Medium' | 'High' // 마이그레이션 복잡도
  estimatedEffort?: string // 예상 작업량
}

/**
 * 인벤토리 응답 타입
 */
export interface InventoryResponse {
  uuid: string
  pqcReadinessScore: number // 0.0-10.0
  algorithmRatios: Record<string, number>
  inventory: CryptographicAsset[]
}

/**
 * 네트워크 지연 시뮬레이션 (0.5-1초)
 */
const simulateNetworkDelay = (): Promise<void> => {
  const delay = 500 + Math.random() * 500 // 0.5-1초
  return new Promise((resolve) => setTimeout(resolve, delay))
}

/**
 * 인벤토리 서비스
 */
export const inventoryService = {
  /**
   * 스캔 인벤토리 조회
   * Mock: 요구사항에 맞는 더미 데이터 반환
   */
  async getScanInventory(uuid: string): Promise<InventoryResponse> {
    try {
      // 네트워크 지연 시뮬레이션
      await simulateNetworkDelay()

      // 실제 API 호출 (현재는 mock)
      // const response = await apiClient.get<InventoryResponse>(`/scans/${uuid}/inventory`)
      // return response.data

      // localStorage에서 캐시 확인
      const inventoryKey = `pqc-scanner-inventory-${uuid}`
      const cached = localStorage.getItem(inventoryKey)
      if (cached) {
        return JSON.parse(cached) as InventoryResponse
      }

      // 요구사항에 맞는 Mock 인벤토리 데이터
      const mockInventory: InventoryResponse = {
        uuid,
        pqcReadinessScore: 7.2, // 72점 (중간 위험 수준)
        algorithmRatios: {
          'RSA-1024': 0.4,
          'SHA-1': 0.35,
          'AES-128': 0.25,
        },
        inventory: [
          {
            id: '1',
            algorithmType: 'RSA-1024',
            filePath: 'src/auth.c',
            lineNumbers: [15, 23, 45],
            riskScore: 9.2, // HIGH 위험도
          },
          {
            id: '2',
            algorithmType: 'SHA-1',
            filePath: 'src/utils/hash.py',
            lineNumbers: [12, 34, 56],
            riskScore: 7.5, // MEDIUM 위험도
          },
          {
            id: '3',
            algorithmType: 'AES-128',
            filePath: 'config/settings.json',
            lineNumbers: [8],
            riskScore: 4.8, // LOW 위험도
          },
        ],
      }

      // localStorage에 저장 (나중에 재사용)
      localStorage.setItem(inventoryKey, JSON.stringify(mockInventory))

      return mockInventory
    } catch (error) {
      logError('Failed to get scan inventory', error)
      throw handleError(error) as AppError
    }
  },

  /**
   * 특정 암호화 자산 상세 정보 조회
   * Mock: 요구사항에 맞는 상세 더미 데이터 반환
   */
  async getAssetDetail(uuid: string, assetId: string): Promise<AssetDetail> {
    try {
      // 네트워크 지연 시뮬레이션
      await simulateNetworkDelay()

      // 실제 API 호출 (현재는 mock)
      // const response = await apiClient.get<AssetDetail>(`/scans/${uuid}/inventory/${assetId}`)
      // return response.data

      // 먼저 인벤토리에서 기본 정보 가져오기
      const inventory = await this.getScanInventory(uuid)
      const baseAsset = inventory.inventory.find((asset) => asset.id === assetId)

      if (!baseAsset) {
        throw new Error(`Asset with ID ${assetId} not found`)
      }

      // Mock 상세 정보 생성 (알고리즘 타입에 따라 다른 정보)
      const mockDetails: Record<string, Partial<AssetDetail>> = {
        '1': {
          // RSA-1024
          keySize: 1024,
          modeOfOperation: 'N/A (Asymmetric)',
          implementation: 'OpenSSL',
          standard: 'RFC 3447 (PKCS#1 v1.5)',
          paddingScheme: 'PKCS#1 v1.5',
          detectedPattern: 'RSA_generate_key(1024, RSA_F4, NULL, NULL)',
          codeSnippet: `// Line 15: RSA key generation
RSA *rsa = RSA_new();
BIGNUM *e = BN_new();
BN_set_word(e, RSA_F4);
RSA_generate_key(1024, RSA_F4, NULL, NULL);

// Line 23: RSA encryption
unsigned char *encrypted = malloc(RSA_size(rsa));
RSA_public_encrypt(data_len, data, encrypted, rsa, RSA_PKCS1_PADDING);

// Line 45: RSA decryption
unsigned char *decrypted = malloc(RSA_size(rsa));
RSA_private_decrypt(encrypted_len, encrypted, decrypted, rsa, RSA_PKCS1_PADDING);`,
          suggestedPQCAlternatives: ['CRYSTALS-Kyber-768', 'CRYSTALS-Kyber-1024', 'NTRU'],
          migrationComplexity: 'High',
          estimatedEffort: '5-7 M/D',
        },
        '2': {
          // SHA-1
          keySize: 160,
          modeOfOperation: 'N/A (Hash Function)',
          implementation: 'Python hashlib',
          standard: 'FIPS PUB 180-4',
          detectedPattern: 'hashlib.sha1()',
          codeSnippet: `# Line 12: SHA-1 hash initialization
import hashlib
hash_obj = hashlib.sha1()

# Line 34: SHA-1 hash update
hash_obj.update(data.encode('utf-8'))

# Line 56: SHA-1 hash finalization
digest = hash_obj.hexdigest()
print(f"SHA-1 Hash: {digest}")`,
          suggestedPQCAlternatives: ['SHA-3-256', 'SHA-3-512', 'BLAKE3'],
          migrationComplexity: 'Medium',
          estimatedEffort: '2-3 M/D',
        },
        '3': {
          // AES-128
          keySize: 128,
          modeOfOperation: 'CBC',
          implementation: 'Node.js crypto',
          standard: 'FIPS PUB 197',
          keyDerivationFunction: 'PBKDF2',
          detectedPattern: 'crypto.createCipheriv("aes-128-cbc", key, iv)',
          codeSnippet: `// Line 8: AES-128-CBC encryption
const crypto = require('crypto');
const algorithm = 'aes-128-cbc';
const key = crypto.randomBytes(16); // 128 bits
const iv = crypto.randomBytes(16);

const cipher = crypto.createCipheriv(algorithm, key, iv);
let encrypted = cipher.update(JSON.stringify(data), 'utf8', 'hex');
encrypted += cipher.final('hex');`,
          suggestedPQCAlternatives: ['AES-256-GCM', 'ChaCha20-Poly1305'],
          migrationComplexity: 'Low',
          estimatedEffort: '1-2 M/D',
        },
      }

      const detailData = mockDetails[assetId] || {}

      return {
        ...baseAsset,
        ...detailData,
      } as AssetDetail
    } catch (error) {
      logError('Failed to get asset detail', error)
      throw handleError(error) as AppError
    }
  },
}
