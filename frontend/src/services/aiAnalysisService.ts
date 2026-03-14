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

export interface AiAffectedLocation {
  file_path: string
  line_start?: number | null
  line_end?: number | null
  rule_id?: string | null
  scanner_type?: string | null
  evidence_excerpt?: string | null
}

export interface AiCodeFixExample {
  file_path: string
  language?: string | null
  rationale: string
  before_code: string
  after_code: string
  confidence: number
}

export interface AiAnalysisRecommendation {
  title: string
  description: string
  nist_standard_reference: string
  affected_locations?: AiAffectedLocation[]
  code_fix_examples?: AiCodeFixExample[]
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
  analysis_mode?: 'real' | 'fallback' | 'mock' | 'error'
  rag_corpus_loaded?: boolean
  rag_chunks_retrieved?: number
  citations_available?: boolean
  llm_model_used?: string | null
  embedding_model_used?: string | null
  vector_store_collection?: string | null
  debug_message?: string | null
  failure_reason?: string | null
}

interface StartAiAnalysisResponse {
  status: string
  scan_id: string
  ai_analysis_id?: string | null
}

interface StartAnalysisOptions {
  force?: boolean
}

interface EnsureAnalysisOptions {
  maxAttempts?: number
  intervalMs?: number
  forceRefresh?: boolean
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

const delay = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms))

const inflightEnsureAnalysis = new Map<string, Promise<AiAnalysisResponse>>()
const DEFAULT_MAX_ATTEMPTS = 300
const DEFAULT_INTERVAL_MS = 1000

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
  analysis_mode: 'mock',
  rag_corpus_loaded: false,
  rag_chunks_retrieved: 0,
  citations_available: false,
  llm_model_used: null,
  embedding_model_used: null,
  vector_store_collection: null,
  debug_message: 'Development mock fallback response.',
  failure_reason: 'VITE_ENABLE_DEV_FALLBACKS=true',
  inputs_summary: {
    counts_by_scanner_type: { SAST: 2, SCA: 1 },
    top_rules: ['rsa_generation', 'weak_hash'],
  },
})

export const aiAnalysisService = {
  async startAnalysis(uuid: string, options?: StartAnalysisOptions): Promise<StartAiAnalysisResponse> {
    const query = options?.force ? '?force=true' : ''
    const response = await apiClient.post<StartAiAnalysisResponse>(`/scans/${uuid}/ai-analysis${query}`)
    return response.data
  },

  async getAnalysis(uuid: string): Promise<AiAnalysisResponse> {
    const response = await apiClient.get<AiAnalysisResponse>(`/scans/${uuid}/ai-analysis`)
    return response.data
  },

  async ensureAnalysis(uuid: string, options?: EnsureAnalysisOptions): Promise<AiAnalysisResponse> {
    const forceRefresh = Boolean(options?.forceRefresh)
    const cacheKey = `${uuid}:${forceRefresh ? 'force' : 'default'}`
    const maxAttempts = options?.maxAttempts ?? DEFAULT_MAX_ATTEMPTS
    const intervalMs = options?.intervalMs ?? DEFAULT_INTERVAL_MS

    if (!forceRefresh) {
      const inflight = inflightEnsureAnalysis.get(cacheKey)
      if (inflight) {
        return inflight
      }
    }

    const task = (async () => {
      if (!forceRefresh) {
        try {
          return await this.getAnalysis(uuid)
        } catch (error) {
          const appError = toAppError(error)
          if (!(appError.type === ErrorType.API_ERROR && appError.statusCode === 404)) {
            if (shouldUseDevFallback(appError)) {
              return buildMockAiAnalysis()
            }
            throw appError
          }
        }
      }

      try {
        await this.startAnalysis(uuid, { force: forceRefresh })
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
        statusCode: 202,
        message: `AI analysis is still being generated (waited ${(maxAttempts * intervalMs) / 1000}s). Please try again shortly.`,
      }
      logError('AI analysis polling timed out', timeoutError)
      throw timeoutError
    })().finally(() => {
      inflightEnsureAnalysis.delete(cacheKey)
    })
    inflightEnsureAnalysis.set(cacheKey, task)
    return task
  },
}
