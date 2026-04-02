import { apiClient } from '../api'
import {
  aiAnalysisService,
  type AiAffectedLocation,
  type AiAnalysisRecommendation,
  type AiCitation,
  type AiCodeFixExample,
} from './aiAnalysisService'
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
  affectedLocations?: AiAffectedLocation[]
  codeFixExamples?: AiCodeFixExample[]
  citations?: AiCitation[]
  confidence?: number
  analysisSummary?: string
  citationMissing?: boolean
  inputsSummary?: Record<string, unknown>
  normalizedClass?: string
  priorityReason?: string
  evidenceCount?: number
  affectedFilesCount?: number
  affectedFilePaths?: string[]
  scannerTypes?: string[]
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
  if (!config.isDevelopment || !config.enableDevFallbacks) {
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
      aiRecommendation:
        '## Replace RSA-1024 with Kyber-768\n\nMigrate quantum-vulnerable key exchange to ML-KEM.',
      normalizedClass: 'rsa-public-key',
      priorityReason: 'RSA class risk, auth-facing usage, development fallback data',
      evidenceCount: 2,
      affectedFilesCount: 1,
      affectedFilePaths: ['src/auth.c'],
      scannerTypes: ['SAST'],
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
      aiRecommendation:
        '## Replace SHA-1 with SHA-3\n\nRemove weak hash usage and adopt SHA-3-compatible paths.',
      normalizedClass: 'weak-hash',
      priorityReason: 'Weak hash usage remains migration debt and lowers trust',
      evidenceCount: 1,
      affectedFilesCount: 1,
      affectedFilePaths: ['src/utils/hash.py'],
      scannerTypes: ['SAST'],
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
  if (text.includes('ecc') || text.includes('ecdsa') || text.includes('elliptic')) {
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

const inferNormalizedClass = (targetAlgorithm: string): string => {
  const normalized = targetAlgorithm.toLowerCase()
  if (normalized.includes('rsa')) {
    return 'rsa-public-key'
  }
  if (normalized.includes('dh')) {
    return 'dh-key-exchange'
  }
  if (normalized.includes('ecc') || normalized.includes('ecdsa')) {
    return 'ecc-signature'
  }
  if (normalized === 'dsa' || normalized.includes('dsa')) {
    return 'dsa-signature'
  }
  if (normalized.includes('weak hash') || normalized.includes('sha-1') || normalized.includes('md5')) {
    return 'weak-hash'
  }
  return 'legacy-library'
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

const uniq = (values: Array<string | null | undefined>): string[] => {
  return Array.from(
    new Set(
      values
        .map((value) => (value ?? '').trim())
        .filter(Boolean),
    ),
  )
}

const getAiFindingSummary = (recommendation: AiAnalysisRecommendation) => {
  const affectedLocations = recommendation.affected_locations ?? []
  const affectedFilePaths = uniq(affectedLocations.map((location) => location.file_path))
  const scannerTypes = uniq(affectedLocations.map((location) => location.scanner_type))

  return {
    affectedLocations,
    affectedFilePaths,
    affectedFilesCount: affectedFilePaths.length,
    scannerTypes,
  }
}

const mapAiAnalysisToRecommendations = (
  uuid: string,
  payload: Awaited<ReturnType<typeof aiAnalysisService.ensureAnalysis>>,
): RecommendationsResponse => {
  if (payload.recommendations.length === 0) {
    return { uuid, recommendations: [] }
  }

  const recommendations: Recommendation[] = payload.recommendations.map((recommendation, index) => {
    const priorityRank = payload.priority_rank + index
    const confidence = recommendation.confidence || payload.confidence_score
    const targetAlgorithm = inferTargetAlgorithm(recommendation)
    const normalizedClass = inferNormalizedClass(targetAlgorithm)
    const summary = getAiFindingSummary(recommendation)
    const primaryLocation = summary.affectedLocations[0]

    return {
      id: `${uuid}-ai-${index + 1}`,
      priorityRank,
      priority: rankToPriority(priorityRank),
      issueName: recommendation.title,
      estimatedEffort: getEffortFromCostLevel(payload.refactor_cost_estimate.level),
      aiRecommendation: formatAiRecommendation(recommendation, payload.analysis_summary, confidence),
      recommendedPQCAlgorithm: inferRecommendedPqc(recommendation),
      targetAlgorithm,
      context: payload.analysis_summary,
      filePath: primaryLocation?.file_path,
      nistStandardReference: recommendation.nist_standard_reference,
      affectedLocations: summary.affectedLocations,
      codeFixExamples: recommendation.code_fix_examples ?? [],
      citations: recommendation.citations,
      confidence,
      analysisSummary: payload.analysis_summary,
      citationMissing: payload.citation_missing,
      inputsSummary: payload.inputs_summary,
      normalizedClass,
      affectedFilesCount: summary.affectedFilesCount,
      affectedFilePaths: summary.affectedFilePaths,
      scannerTypes: summary.scannerTypes,
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

const getCanonicalClassKey = (recommendation: Recommendation): string => {
  if (hasMeaningfulText(recommendation.normalizedClass)) {
    return recommendation.normalizedClass.trim().toLowerCase()
  }
  return inferNormalizedClass(recommendation.targetAlgorithm)
}

const mergeRecommendationData = (
  plannerResponse: RecommendationsResponse,
  aiResponse: RecommendationsResponse,
): RecommendationsResponse => {
  if (plannerResponse.recommendations.length === 0) {
    return aiResponse
  }

  const aiByClass = new Map<string, Recommendation>()
  aiResponse.recommendations.forEach((recommendation) => {
    const classKey = getCanonicalClassKey(recommendation)
    if (!aiByClass.has(classKey)) {
      aiByClass.set(classKey, recommendation)
    }
  })

  return {
    uuid: plannerResponse.uuid,
    recommendations: plannerResponse.recommendations.map((plannerRecommendation) => {
      const aiRecommendation = aiByClass.get(getCanonicalClassKey(plannerRecommendation))
      if (!aiRecommendation) {
        return plannerRecommendation
      }

      return {
        ...plannerRecommendation,
        aiRecommendation: aiRecommendation.aiRecommendation || plannerRecommendation.aiRecommendation,
        nistStandardReference:
          aiRecommendation.nistStandardReference || plannerRecommendation.nistStandardReference,
        affectedLocations: aiRecommendation.affectedLocations,
        codeFixExamples: aiRecommendation.codeFixExamples,
        citations: aiRecommendation.citations,
        confidence: aiRecommendation.confidence,
        analysisSummary: aiRecommendation.analysisSummary || plannerRecommendation.analysisSummary,
        citationMissing: aiRecommendation.citationMissing,
        inputsSummary: aiRecommendation.inputsSummary,
      }
    }),
  }
}

const getPlannerRecommendations = async (uuid: string): Promise<RecommendationsResponse> => {
  const response = await apiClient.get<RecommendationsResponse>(`/scans/${uuid}/recommendations`)
  return response.data
}

export const aiRecommendationService = {
  async getRecommendations(
    uuid: string,
    filters?: {
      algorithmType?: string
      priority?: Priority
    },
    options?: {
      forceAnalysisRefresh?: boolean
    },
  ): Promise<RecommendationsResponse> {
    let plannerResponse: RecommendationsResponse | null = null

    try {
      plannerResponse = await getPlannerRecommendations(uuid)
    } catch (error) {
      const appError = toAppError(error)
      logError('Failed to get canonical recommendations', appError)
      if (!shouldUseDevFallback(appError) && !(appError.type === ErrorType.API_ERROR && appError.statusCode === 404)) {
        throw appError
      }
    }

    try {
      const aiAnalysis = await aiAnalysisService.ensureAnalysis(uuid, {
        forceRefresh: Boolean(options?.forceAnalysisRefresh),
      })
      const aiResponse = mapAiAnalysisToRecommendations(uuid, aiAnalysis)
      const merged = plannerResponse ? mergeRecommendationData(plannerResponse, aiResponse) : aiResponse
      return applyFilters(merged, filters)
    } catch (error) {
      const appError = toAppError(error)
      logError('Failed to get AI recommendations', appError)

      if (plannerResponse) {
        return applyFilters(plannerResponse, filters)
      }

      if (shouldUseDevFallback(appError)) {
        return applyFilters({ uuid, recommendations: generateMockRecommendations() }, filters)
      }

      throw appError
    }
  },
}
