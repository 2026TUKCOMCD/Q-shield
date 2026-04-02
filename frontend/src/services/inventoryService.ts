import { apiClient } from '../api'
import { config } from '../config'
import { handleError, type AppError, ErrorType } from '../utils/errorHandler'
import { logError } from '../utils/logger'

export interface CryptographicAsset {
  id: string
  algorithmType: string
  filePath: string
  lineNumbers: number[]
  riskScore: number
}

export interface AssetDetail extends CryptographicAsset {
  keySize?: number
  modeOfOperation?: string
  implementation?: string
  standard?: string
  keyDerivationFunction?: string
  paddingScheme?: string
  codeSnippet?: string
  codeSnippetStartLine?: number
  detectedPattern?: string
  suggestedPQCAlternatives?: string[]
  migrationComplexity?: 'Low' | 'Medium' | 'High'
  estimatedEffort?: string
}

export interface InventoryResponse {
  uuid: string
  pqcReadinessScore: number
  algorithmRatios: Record<string, number>
  inventory: CryptographicAsset[]
}

export interface InventorySignals {
  classLabel: string
  classReason: string
  boundaryLabel: string
  trustLabel: string
}

const isAppError = (error: unknown): error is AppError => {
  return typeof error === 'object' && error !== null && 'type' in error && 'message' in error
}

const toAppError = (error: unknown): AppError => {
  return isAppError(error) ? error : (handleError(error) as AppError)
}

const shouldUseDevFallback = (error: AppError): boolean => {
  if (!config.isDevelopment || !config.enableDevFallbacks) {
    return false
  }
  if (error.type === ErrorType.NETWORK_ERROR) {
    return true
  }
  return error.type === ErrorType.API_ERROR && (error.statusCode ?? 0) >= 500
}

const generateMockInventory = (uuid: string): InventoryResponse => {
  return {
    uuid,
    pqcReadinessScore: 7.2,
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
        riskScore: 9.2,
      },
      {
        id: '2',
        algorithmType: 'SHA-1',
        filePath: 'src/utils/hash.py',
        lineNumbers: [12, 34, 56],
        riskScore: 7.5,
      },
      {
        id: '3',
        algorithmType: 'AES-128',
        filePath: 'config/settings.json',
        lineNumbers: [8],
        riskScore: 4.8,
      },
    ],
  }
}

const fallbackAssetDetails: Record<string, Partial<AssetDetail>> = {
  '1': {
    keySize: 1024,
    modeOfOperation: 'N/A (Asymmetric)',
    implementation: 'OpenSSL',
    standard: 'RFC 3447 (PKCS#1 v1.5)',
    paddingScheme: 'PKCS#1 v1.5',
    detectedPattern: 'RSA_generate_key(1024, RSA_F4, NULL, NULL)',
    suggestedPQCAlternatives: ['CRYSTALS-Kyber-768', 'CRYSTALS-Kyber-1024', 'NTRU'],
    migrationComplexity: 'High',
    estimatedEffort: '5-7 M/D',
  },
  '2': {
    keySize: 160,
    modeOfOperation: 'N/A (Hash Function)',
    implementation: 'Python hashlib',
    standard: 'FIPS PUB 180-4',
    detectedPattern: 'hashlib.sha1()',
    suggestedPQCAlternatives: ['SHA-3-256', 'SHA-3-512', 'BLAKE3'],
    migrationComplexity: 'Medium',
    estimatedEffort: '2-3 M/D',
  },
  '3': {
    keySize: 128,
    modeOfOperation: 'CBC',
    implementation: 'Node.js crypto',
    standard: 'FIPS PUB 197',
    keyDerivationFunction: 'PBKDF2',
    detectedPattern: 'crypto.createCipheriv("aes-128-cbc", key, iv)',
    suggestedPQCAlternatives: ['AES-256-GCM', 'ChaCha20-Poly1305'],
    migrationComplexity: 'Low',
    estimatedEffort: '1-2 M/D',
  },
}

export const inferInventorySignals = (asset: CryptographicAsset): InventorySignals => {
  const algorithm = asset.algorithmType.toLowerCase()
  const filePath = asset.filePath.toLowerCase()
  const lineHitCount = asset.lineNumbers.length

  let classLabel = 'Legacy crypto signal'
  let classReason = 'Review this asset during migration planning.'

  if (
    algorithm.includes('rsa') ||
    algorithm.includes('ecc') ||
    algorithm.includes('ecdsa') ||
    algorithm.includes('dsa') ||
    algorithm.includes('dh')
  ) {
    classLabel = 'Quantum-vulnerable public-key'
    classReason = 'Public-key algorithms are primary PQC migration targets.'
  } else if (algorithm.includes('sha-1') || algorithm.includes('sha1') || algorithm.includes('md5')) {
    classLabel = 'Weak hash debt'
    classReason = 'Weak hash usage should be removed early to reduce migration debt.'
  } else if (algorithm.includes('aes') || algorithm.includes('chacha')) {
    classLabel = 'Symmetric path'
    classReason = 'Symmetric crypto is not the primary PQC replacement target, but still affects readiness.'
  }

  let boundaryLabel = 'Internal code path'
  if (
    filePath.includes('auth') ||
    filePath.includes('token') ||
    filePath.includes('login') ||
    filePath.includes('jwt')
  ) {
    boundaryLabel = 'Auth/token boundary'
  } else if (
    filePath.includes('tls') ||
    filePath.includes('ssl') ||
    filePath.includes('cert') ||
    filePath.includes('nginx') ||
    filePath.includes('gateway')
  ) {
    boundaryLabel = 'TLS/certificate boundary'
  } else if (filePath.includes('config')) {
    boundaryLabel = 'Configuration boundary'
  }

  const trustLabel =
    lineHitCount > 1 ? `Static evidence across ${lineHitCount} lines` : 'Single static evidence location'

  return {
    classLabel,
    classReason,
    boundaryLabel,
    trustLabel,
  }
}

export const inventoryService = {
  async getScanInventory(uuid: string): Promise<InventoryResponse> {
    try {
      const response = await apiClient.get<InventoryResponse>(`/scans/${uuid}/inventory`)
      return response.data
    } catch (error) {
      const appError = toAppError(error)
      logError('Failed to get scan inventory', appError)

      if (shouldUseDevFallback(appError)) {
        return generateMockInventory(uuid)
      }

      throw appError
    }
  },

  async getAssetDetail(uuid: string, assetId: string): Promise<AssetDetail> {
    try {
      const encodedAssetId = encodeURIComponent(assetId)
      const response = await apiClient.get<AssetDetail>(`/scans/${uuid}/inventory/${encodedAssetId}`)
      return response.data
    } catch (error) {
      const appError = toAppError(error)
      logError('Failed to get asset detail', appError)

      if (shouldUseDevFallback(appError)) {
        const inventory = generateMockInventory(uuid)
        const baseAsset = inventory.inventory.find((asset) => asset.id === assetId)
        if (!baseAsset) {
          throw appError
        }
        return {
          ...baseAsset,
          ...(fallbackAssetDetails[assetId] || {}),
        }
      }

      throw appError
    }
  },
}

