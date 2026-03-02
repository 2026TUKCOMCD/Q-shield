import { apiClient } from '../api'
import { config } from '../config'
import { handleError, type AppError, ErrorType } from '../utils/errorHandler'
import { logError } from '../utils/logger'

export interface AiCitation {
  doc_id: string
  title: string
  section: string
  page?: number | null
  url?: string | null
  snippet: string
}

export interface AiAnalysisRecommendation {
  title: string
  description: string
  nist_standard_reference: string
  citations: AiCitation[]
  confidence: number
}

export interface AiRefactorCostEstimate {
  level: 'LOW' | 'MEDIUM' | 'HIGH'
  explanation: string
  affected_files: number
}

export interface AiAnalysisResponse {
  risk_score: number
  pqc_readiness_score: number
  severity_weighted_index: number
  refactor_cost_estimate: AiRefactorCostEstimate
  priority_rank: number
  recommendations: AiAnalysisRecommendation[]
  analysis_summary: string
  confidence_score: number
  citation_missing: boolean
  inputs_summary: Record<string, unknown>
}

interface StartAiAnalysisResponse {
  status: string
  scan_id: string
  ai_analysis_id?: string | null
}

const isAppError = (error: unknown): error is AppError => {
  return typeof error === 'object' && error !== null && 'type' in error && 'message' in error
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

const delay = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms))

const buildMockAiAnalysis = (): AiAnalysisResponse => ({
  risk_score: 64,
  pqc_readiness_score: 50,
  severity_weighted_index: 1.42,
  refactor_cost_estimate: {
    level: 'MEDIUM',
    explanation: '7 files affected, moderate usage density across legacy modules.',
    affected_files: 7,
  },
  priority_rank: 2,
  recommendations: [
    {
      title: 'Migrate RSA signatures to ML-DSA (Dilithium)',
      description: 'RSA and weak-hash patterns are present in the authentication path. Replace quantum-vulnerable signatures and remove weak hash dependencies first.',
      nist_standard_reference: 'FIPS 204 (ML-DSA)',
      citations: [],
      confidence: 0.73,
    },
    {
      title: 'Replace key establishment flows with ML-KEM (Kyber)',
      description: 'For any RSA-based key establishment or hybrid exchange, adopt ML-KEM-capable libraries such as liboqs integrations.',
      nist_standard_reference: 'FIPS 203 (ML-KEM)',
      citations: [],
      confidence: 0.7,
    },
  ],
  analysis_summary: 'Mock AI analysis generated in development fallback mode.',
  confidence_score: 0.71,
  citation_missing: true,
  inputs_summary: {
    counts_by_scanner_type: { SAST: 2, SCA: 1 },
    top_rules: ['rsa_generation', 'weak_hash'],
  },
})

export const aiAnalysisService = {
  async startAnalysis(uuid: string): Promise<StartAiAnalysisResponse> {
    const response = await apiClient.post<StartAiAnalysisResponse>(`/scans/${uuid}/ai-analysis`)
    return response.data
  },

  async getAnalysis(uuid: string): Promise<AiAnalysisResponse> {
    const response = await apiClient.get<AiAnalysisResponse>(`/scans/${uuid}/ai-analysis`)
    return response.data
  },

  async ensureAnalysis(
    uuid: string,
    options?: {
      maxAttempts?: number
      intervalMs?: number
    },
  ): Promise<AiAnalysisResponse> {
    const maxAttempts = options?.maxAttempts ?? 10
    const intervalMs = options?.intervalMs ?? 1000

    try {
      await this.startAnalysis(uuid)
    } catch (error) {
      const appError = toAppError(error)
      if (!shouldUseDevFallback(appError)) {
        throw appError
      }
      return buildMockAiAnalysis()
    }

    for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
      try {
        return await this.getAnalysis(uuid)
      } catch (error) {
        const appError = toAppError(error)

        if (appError.type === ErrorType.API_ERROR && appError.statusCode === 404) {
          await delay(intervalMs)
          continue
        }

        if (shouldUseDevFallback(appError)) {
          return buildMockAiAnalysis()
        }

        throw appError
      }
    }

    const timeoutError: AppError = {
      type: ErrorType.API_ERROR,
      statusCode: 404,
      message: 'AI analysis is still being generated. Please try again shortly.',
    }
    logError('AI analysis polling timed out', timeoutError)
    throw timeoutError
  },
}
