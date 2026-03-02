import { apiClient } from '../api'
import { aiAnalysisService, type AiAnalysisRecommendation, type AiCitation } from './aiAnalysisService'
import { config } from '../config'
import { handleError, type AppError, ErrorType } from '../utils/errorHandler'
import { logError } from '../utils/logger'

export type Priority = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'

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
  nistStandardReference?: string
  citations?: AiCitation[]
  confidence?: number
  analysisSummary?: string
  citationMissing?: boolean
  inputsSummary?: Record<string, unknown>
}

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

const generateMockRecommendations = (): Recommendation[] => {
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
      nistStandardReference: 'FIPS 203 (ML-KEM)',
      citations: [],
      confidence: 0.7,
      analysisSummary: 'Development fallback response.',
      aiRecommendation: '## Replace RSA-1024 with Kyber-768\n\nMigrate quantum-vulnerable key exchange to ML-KEM.',
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
      nistStandardReference: 'SP 800-131A Rev. 2',
      citations: [],
      confidence: 0.68,
      analysisSummary: 'Development fallback response.',
      aiRecommendation: '## Replace SHA-1 with SHA-3\n\nRemove weak hash usage and adopt SHA-3-compatible paths.',
    },
  ]
}

const rankToPriority = (rank: number): Priority => {
  if (rank <= 2) {
    return 'CRITICAL'
  }
  if (rank <= 5) {
    return 'HIGH'
  }
  if (rank <= 8) {
    return 'MEDIUM'
  }
  return 'LOW'
}

const getEffortFromCostLevel = (level: 'LOW' | 'MEDIUM' | 'HIGH'): string => {
  switch (level) {
    case 'HIGH':
      return '5-8 M/D'
    case 'MEDIUM':
      return '3-5 M/D'
    case 'LOW':
      return '1-2 M/D'
  }
}

const hasMeaningfulText = (value?: string | null): value is string => {
  if (!value) {
    return false
  }

  const normalizedValue = value.trim()
  return normalizedValue !== '' && normalizedValue.toUpperCase() !== 'N/A'
}

const inferTargetAlgorithm = (recommendation: AiAnalysisRecommendation): string => {
  const text = `${recommendation.title} ${recommendation.description}`.toLowerCase()
  if (text.includes('rsa')) {
    return 'RSA'
  }
  if (text.includes('ecc') || text.includes('ecdsa')) {
    return 'ECC/ECDSA'
  }
  if (text.includes('dsa')) {
    return 'DSA'
  }
  if (text.includes('sha-1') || text.includes('sha1') || text.includes('md5') || text.includes('weak hash')) {
    return 'Weak Hash'
  }
  if (text.includes('dh') || text.includes('diffie')) {
    return 'DH/ECDH'
  }
  return 'Legacy Crypto'
}

const inferRecommendedPqc = (recommendation: AiAnalysisRecommendation): string => {
  const text = `${recommendation.title} ${recommendation.nist_standard_reference}`.toLowerCase()
  if (text.includes('ml-kem') || text.includes('kyber')) {
    return 'ML-KEM (Kyber)'
  }
  if (text.includes('ml-dsa') || text.includes('dilithium')) {
    return 'ML-DSA (Dilithium)'
  }
  return hasMeaningfulText(recommendation.nist_standard_reference)
    ? recommendation.nist_standard_reference
    : 'PQC Migration'
}

const formatAiRecommendation = (
  recommendation: AiAnalysisRecommendation,
  analysisSummary: string,
  confidenceScore: number,
): string => {
  const lines = [
    `## ${recommendation.title}`,
    recommendation.description,
    '',
    '### NIST Standard Reference',
    hasMeaningfulText(recommendation.nist_standard_reference)
      ? recommendation.nist_standard_reference
      : 'Not available',
    '',
    '### Confidence',
    `${Math.round(confidenceScore * 100)}%`,
  ]

  if (analysisSummary) {
    lines.push('', '### Analysis Summary', analysisSummary)
  }

  if (recommendation.citations.length > 0) {
    lines.push('', '### Supporting Citations')
    recommendation.citations.forEach((citation) => {
      const pageText = citation.page ? `, p.${citation.page}` : ''
      lines.push(`- ${citation.title} (${citation.section}${pageText})`)
      lines.push(`  ${citation.snippet}`)
    })
  }

  return lines.join('\n')
}

const mapAiAnalysisToRecommendations = (
  uuid: string,
  payload: Awaited<ReturnType<typeof aiAnalysisService.ensureAnalysis>>,
): RecommendationsResponse => {
  const recommendations: Recommendation[] = payload.recommendations.map((recommendation, index) => {
    const priorityRank = payload.priority_rank + index
    const confidence = recommendation.confidence || payload.confidence_score

    return {
      id: `${uuid}-ai-${index + 1}`,
      priorityRank,
      priority: rankToPriority(priorityRank),
      issueName: recommendation.title,
      estimatedEffort: getEffortFromCostLevel(payload.refactor_cost_estimate.level),
      aiRecommendation: formatAiRecommendation(recommendation, payload.analysis_summary, confidence),
      recommendedPQCAlgorithm: inferRecommendedPqc(recommendation),
      targetAlgorithm: inferTargetAlgorithm(recommendation),
      context: payload.analysis_summary,
      nistStandardReference: recommendation.nist_standard_reference,
      citations: recommendation.citations,
      confidence,
      analysisSummary: payload.analysis_summary,
      citationMissing: payload.citation_missing,
      inputsSummary: payload.inputs_summary,
    }
  })

  return { uuid, recommendations }
}

const applyFilters = (
  response: RecommendationsResponse,
  filters?: {
    algorithmType?: string
    priority?: Priority
  },
): RecommendationsResponse => {
  let recommendations = response.recommendations

  if (filters?.algorithmType) {
    const tokens = filters.algorithmType
      .split(',')
      .map((token) => token.trim().toLowerCase())
      .filter(Boolean)

    if (tokens.length > 0) {
      recommendations = recommendations.filter((rec) => {
        const targetAlgorithm = rec.targetAlgorithm.toLowerCase()
        return tokens.some((token) => targetAlgorithm.includes(token))
      })
    }
  }

  if (filters?.priority) {
    recommendations = recommendations.filter((rec) => rec.priority === filters.priority)
  }

  return {
    ...response,
    recommendations,
  }
}

export const aiRecommendationService = {
  async getRecommendations(
    uuid: string,
    filters?: {
      algorithmType?: string
      priority?: Priority
    },
  ): Promise<RecommendationsResponse> {
    try {
      const aiAnalysis = await aiAnalysisService.ensureAnalysis(uuid)
      return applyFilters(mapAiAnalysisToRecommendations(uuid, aiAnalysis), filters)
    } catch (error) {
      const appError = toAppError(error)
      logError('Failed to get AI recommendations', appError)

      if (appError.type === ErrorType.API_ERROR && appError.statusCode === 404) {
        try {
          const response = await apiClient.get<RecommendationsResponse>(`/scans/${uuid}/recommendations`)
          return applyFilters(response.data, filters)
        } catch (legacyError) {
          const legacyAppError = toAppError(legacyError)
          logError('Failed to get legacy recommendations', legacyAppError)
          if (!shouldUseDevFallback(legacyAppError)) {
            throw legacyAppError
          }
        }
      }

      if (shouldUseDevFallback(appError)) {
        return applyFilters({ uuid, recommendations: generateMockRecommendations() }, filters)
      }

      throw appError
    }
  },
}
