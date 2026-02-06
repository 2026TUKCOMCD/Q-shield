import { apiClient } from '../api'
import { config } from '../config'
import { handleError, type AppError, ErrorType } from '../utils/errorHandler'
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
  estimatedEffort: string
  aiRecommendation: string
  recommendedPQCAlgorithm: string
  targetAlgorithm: string
  context: string
  filePath?: string
}

/**
 * 추천사항 응답 타입
 */
export interface RecommendationsResponse {
  uuid: string
  recommendations: Recommendation[]
}

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
      aiRecommendation: '## Why this is a risk\n\nRSA-1024 is vulnerable to quantum attacks.',
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
      aiRecommendation: '## Why this is a risk\n\nSHA-1 is cryptographically broken.',
    },
  ]
}

/**
 * 추천사항 서비스 (API-first, DEV fallback)
 */
export const recommendationService = {
  async getRecommendations(
    uuid: string,
    filters?: {
      algorithmType?: string
      context?: string
      priority?: Priority
    }
  ): Promise<RecommendationsResponse> {
    try {
      const params = new URLSearchParams()
      if (filters?.algorithmType) {
        params.append('algorithmType', filters.algorithmType)
      }
      if (filters?.context) {
        params.append('context', filters.context)
      }
      if (filters?.priority) {
        params.append('priority', filters.priority)
      }

      const query = params.toString()
      const url = query ? `/scans/${uuid}/recommendations?${query}` : `/scans/${uuid}/recommendations`
      const response = await apiClient.get<RecommendationsResponse>(url)
      return response.data
    } catch (error) {
      const appError = toAppError(error)
      logError('Failed to get recommendations', appError)

      if (shouldUseDevFallback(appError)) {
        let recommendations = generateMockRecommendations(uuid)

        if (filters?.algorithmType) {
          const keyword = filters.algorithmType.toLowerCase()
          recommendations = recommendations.filter(
            (rec) =>
              rec.targetAlgorithm.toLowerCase().includes(keyword) ||
              rec.recommendedPQCAlgorithm.toLowerCase().includes(keyword)
          )
        }
        if (filters?.context) {
          const keyword = filters.context.toLowerCase()
          recommendations = recommendations.filter((rec) => rec.context.toLowerCase().includes(keyword))
        }
        if (filters?.priority) {
          recommendations = recommendations.filter((rec) => rec.priority === filters.priority)
        }

        return { uuid, recommendations }
      }

      throw appError
    }
  },
}
