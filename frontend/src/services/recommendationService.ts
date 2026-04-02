import {
  aiRecommendationService,
  type Priority,
  type Recommendation,
  type RecommendationsResponse,
} from './aiRecommendationService'

export type { Priority, Recommendation, RecommendationsResponse }

// Keep the legacy service name as a compatibility wrapper while using
// the AI-analysis-backed recommendation flow as the single source of truth.
export const recommendationService = {
  async getRecommendations(
    uuid: string,
    filters?: {
      algorithmType?: string
      context?: string
      priority?: Priority
    },
    options?: {
      forceAnalysisRefresh?: boolean
    },
  ): Promise<RecommendationsResponse> {
    const response = await aiRecommendationService.getRecommendations(
      uuid,
      {
        algorithmType: filters?.algorithmType,
        priority: filters?.priority,
      },
      options,
    )

    const contextFilter = (filters?.context || "").trim().toLowerCase()
    if (!contextFilter) {
      return response
    }

    return {
      ...response,
      recommendations: response.recommendations.filter((recommendation) => {
        const haystacks = [
          recommendation.context,
          recommendation.filePath,
          recommendation.analysisSummary,
        ]
        return haystacks.some((value) => (value || "").toLowerCase().includes(contextFilter))
      }),
    }
  },
}
