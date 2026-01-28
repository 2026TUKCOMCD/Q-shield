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
}
