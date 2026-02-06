import { apiClient } from '../api'
import { config } from '../config'
import { handleError, type AppError, ErrorType } from '../utils/errorHandler'
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
  aggregatedRiskScore: number
  children?: RepositoryFile[]
}

/**
 * 히트맵 응답 타입
 */
export type HeatmapResponse = RepositoryFile[]

const isAppError = (error: unknown): error is AppError => {
  return (
    typeof error === 'object' &&
    error !== null &&
    'type' in error &&
    'message' in error
  )
}

const toAppError = (error: unknown): AppError => {
  return isAppError(error) ? error : (handleError(error) as AppError)
}

const shouldUseDevFallback = (error: AppError): boolean => {
  if (!config.isDevelopment) {
    return false
  }
  if (error.type === ErrorType.NETWORK_ERROR) {
    return true
  }
  return error.type === ErrorType.API_ERROR && (error.statusCode ?? 0) >= 500
}

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

const generateMockHeatmap = (): HeatmapResponse => {
  return [
    {
      filePath: 'src',
      fileName: 'src',
      fileType: 'folder',
      aggregatedRiskScore: 8.5,
      children: [
        {
          filePath: 'src/auth.c',
          fileName: 'auth.c',
          fileType: 'file',
          aggregatedRiskScore: 9.2,
        },
      ],
    },
  ]
}

/**
 * 폴더의 최고 리스크 레벨 계산 (재귀)
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
      const childScore = child.aggregatedRiskScore
      if (childScore > maxScore) {
        maxScore = childScore
        maxRisk = getRiskLevel(childScore)
      }
    } else if (child.aggregatedRiskScore > maxScore) {
      maxScore = child.aggregatedRiskScore
      maxRisk = getRiskLevel(child.aggregatedRiskScore)
    }
  }

  return maxRisk
}

/**
 * 폴더 내 취약점 개수 계산 (재귀)
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
 * 히트맵 서비스 (API-first, DEV fallback)
 */
export const heatmapService = {
  async getHeatmap(uuid: string): Promise<HeatmapResponse> {
    try {
      const response = await apiClient.get<HeatmapResponse>(`/scans/${uuid}/heatmap`)
      return response.data
    } catch (error) {
      const appError = toAppError(error)
      logError('Failed to get heatmap', appError)

      if (shouldUseDevFallback(appError)) {
        return generateMockHeatmap()
      }

      throw appError
    }
  },
}
