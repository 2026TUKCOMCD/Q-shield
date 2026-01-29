import { apiClient } from '../api'
import { handleError, type AppError } from '../utils/errorHandler'
import { logError } from '../utils/logger'

/**
 * 리스크 레벨 타입
 */
export type RiskLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'SAFE'

/**
 * 파일 타입
 */
export type FileType = 'file' | 'folder'

/**
 * 리포지토리 파일 노드 타입
 */
export interface RepositoryFile {
  filePath: string
  fileName: string
  fileType: FileType
  aggregatedRiskScore: number // 0.0-10.0
  children?: RepositoryFile[] // 폴더인 경우에만 존재
}

/**
 * 히트맵 응답 타입
 */
export type HeatmapResponse = RepositoryFile[]

/**
 * 리스크 점수를 리스크 레벨로 변환
 */
export const getRiskLevel = (riskScore: number): RiskLevel => {
  if (riskScore >= 8.0) return 'CRITICAL'
  if (riskScore >= 5.0) return 'HIGH'
  if (riskScore >= 3.0) return 'MEDIUM'
  if (riskScore > 0) return 'LOW'
  return 'SAFE'
}

/**
 * 리스크 레벨에 따른 색상 반환
 */
export const getRiskColor = (riskLevel: RiskLevel) => {
  switch (riskLevel) {
    case 'CRITICAL':
      return {
        bg: 'bg-red-500/20',
        border: 'border-red-500/50',
        text: 'text-red-400',
        glow: 'shadow-red-500/50',
      }
    case 'HIGH':
      return {
        bg: 'bg-orange-500/20',
        border: 'border-orange-500/50',
        text: 'text-orange-400',
        glow: 'shadow-orange-500/50',
      }
    case 'MEDIUM':
      return {
        bg: 'bg-yellow-500/20',
        border: 'border-yellow-500/50',
        text: 'text-yellow-400',
        glow: 'shadow-yellow-500/50',
      }
    case 'LOW':
      return {
        bg: 'bg-blue-500/20',
        border: 'border-blue-500/50',
        text: 'text-blue-400',
        glow: 'shadow-blue-500/50',
      }
    case 'SAFE':
      return {
        bg: 'bg-slate-500/20',
        border: 'border-slate-500/30',
        text: 'text-slate-400',
        glow: 'shadow-slate-500/30',
      }
  }
}

/**
 * 네트워크 지연 시뮬레이션 (0.5-1초)
 */
const simulateNetworkDelay = (): Promise<void> => {
  const delay = 500 + Math.random() * 500 // 0.5-1초
  return new Promise((resolve) => setTimeout(resolve, delay))
}

/**
 * Mock 히트맵 데이터 생성
 */
const generateMockHeatmap = (): HeatmapResponse => {
  return [
    {
      filePath: 'src',
      fileName: 'src',
      fileType: 'folder',
      aggregatedRiskScore: 8.5, // CRITICAL
      children: [
        {
          filePath: 'src/auth.c',
          fileName: 'auth.c',
          fileType: 'file',
          aggregatedRiskScore: 9.2, // CRITICAL
        },
        {
          filePath: 'src/utils',
          fileName: 'utils',
          fileType: 'folder',
          aggregatedRiskScore: 7.5, // HIGH
          children: [
            {
              filePath: 'src/utils/hash.py',
              fileName: 'hash.py',
              fileType: 'file',
              aggregatedRiskScore: 7.5, // HIGH
            },
            {
              filePath: 'src/utils/helpers.js',
              fileName: 'helpers.js',
              fileType: 'file',
              aggregatedRiskScore: 2.1, // LOW
            },
          ],
        },
        {
          filePath: 'src/crypto',
          fileName: 'crypto',
          fileType: 'folder',
          aggregatedRiskScore: 6.8, // HIGH
          children: [
            {
              filePath: 'src/crypto/signature.c',
              fileName: 'signature.c',
              fileType: 'file',
              aggregatedRiskScore: 6.8, // HIGH
            },
            {
              filePath: 'src/crypto/encryption.rs',
              fileName: 'encryption.rs',
              fileType: 'file',
              aggregatedRiskScore: 4.2, // MEDIUM
            },
          ],
        },
        {
          filePath: 'src/api',
          fileName: 'api',
          fileType: 'folder',
          aggregatedRiskScore: 3.5, // MEDIUM
          children: [
            {
              filePath: 'src/api/routes.ts',
              fileName: 'routes.ts',
              fileType: 'file',
              aggregatedRiskScore: 3.5, // MEDIUM
            },
            {
              filePath: 'src/api/middleware.ts',
              fileName: 'middleware.ts',
              fileType: 'file',
              aggregatedRiskScore: 1.2, // LOW
            },
          ],
        },
      ],
    },
    {
      filePath: 'config',
      fileName: 'config',
      fileType: 'folder',
      aggregatedRiskScore: 4.8, // MEDIUM
      children: [
        {
          filePath: 'config/settings.json',
          fileName: 'settings.json',
          fileType: 'file',
          aggregatedRiskScore: 4.8, // MEDIUM
        },
        {
          filePath: 'config/database.yml',
          fileName: 'database.yml',
          fileType: 'file',
          aggregatedRiskScore: 0.5, // LOW
        },
      ],
    },
    {
      filePath: 'tests',
      fileName: 'tests',
      fileType: 'folder',
      aggregatedRiskScore: 0.0, // SAFE
      children: [
        {
          filePath: 'tests/unit',
          fileName: 'unit',
          fileType: 'folder',
          aggregatedRiskScore: 0.0, // SAFE
          children: [
            {
              filePath: 'tests/unit/auth.test.js',
              fileName: 'auth.test.js',
              fileType: 'file',
              aggregatedRiskScore: 0.0, // SAFE
            },
          ],
        },
      ],
    },
    {
      filePath: 'README.md',
      fileName: 'README.md',
      fileType: 'file',
      aggregatedRiskScore: 0.0, // SAFE
    },
  ]
}

/**
 * 폴더의 최고 리스크 레벨 계산 (재귀적)
 */
export const calculateFolderMaxRisk = (folder: RepositoryFile): RiskLevel => {
  if (folder.fileType === 'file') {
    return getRiskLevel(folder.aggregatedRiskScore)
  }

  if (!folder.children || folder.children.length === 0) {
    return 'SAFE'
  }

  let maxRisk: RiskLevel = 'SAFE'
  let maxScore = 0

  for (const child of folder.children) {
    if (child.fileType === 'folder') {
      const childRisk = calculateFolderMaxRisk(child)
      const childScore = child.aggregatedRiskScore
      if (childScore > maxScore) {
        maxScore = childScore
        maxRisk = getRiskLevel(childScore)
      }
    } else {
      if (child.aggregatedRiskScore > maxScore) {
        maxScore = child.aggregatedRiskScore
        maxRisk = getRiskLevel(child.aggregatedRiskScore)
      }
    }
  }

  return maxRisk
}

/**
 * 폴더 내 취약점 개수 계산 (재귀적)
 */
export const calculateVulnerabilityCount = (folder: RepositoryFile): number => {
  if (folder.fileType === 'file') {
    return folder.aggregatedRiskScore > 0 ? 1 : 0
  }

  if (!folder.children || folder.children.length === 0) {
    return 0
  }

  let count = 0
  for (const child of folder.children) {
    count += calculateVulnerabilityCount(child)
  }

  return count
}

/**
 * 히트맵 서비스
 */
export const heatmapService = {
  /**
   * 스캔 히트맵 데이터 조회
   * Mock: 요구사항에 맞는 더미 데이터 반환
   */
  async getHeatmap(uuid: string): Promise<HeatmapResponse> {
    try {
      // 네트워크 지연 시뮬레이션
      await simulateNetworkDelay()

      // 실제 API 호출 (현재는 mock)
      // const response = await apiClient.get<HeatmapResponse>(`/scans/${uuid}/heatmap`)
      // return response.data

      // localStorage에서 캐시 확인
      const heatmapKey = `pqc-scanner-heatmap-${uuid}`
      const cached = localStorage.getItem(heatmapKey)

      if (cached) {
        return JSON.parse(cached) as HeatmapResponse
      }

      // Mock 데이터 생성
      const mockHeatmap = generateMockHeatmap()

      // localStorage에 저장
      localStorage.setItem(heatmapKey, JSON.stringify(mockHeatmap))

      return mockHeatmap
    } catch (error) {
      logError('Failed to get heatmap', error)
      throw handleError(error) as AppError
    }
  },
}
