import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  recommendationService,
  type Recommendation,
  type Priority,
} from '../services/recommendationService'
import { RecommendationFilters } from '../components/RecommendationFilters'
import { RecommendationTable } from '../components/RecommendationTable'
import { AIDetailView } from '../components/AIDetailView'
import { logError } from '../utils/logger'
import {
  Loader2,
  AlertCircle,
  ArrowLeft,
  Sparkles,
  XCircle,
} from 'lucide-react'

/**
 * Recommendations 페이지
 * T016: 우선순위별 PQC 마이그레이션 추천사항 표시
 */
export const Recommendations = () => {
  const { uuid } = useParams<{ uuid: string }>()
  const navigate = useNavigate()

  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [filteredRecommendations, setFilteredRecommendations] = useState<Recommendation[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // 필터 상태
  const [algorithmType, setAlgorithmType] = useState('')
  const [context, setContext] = useState('')
  const [priority, setPriority] = useState<Priority | ''>('')

  // AI Detail View 상태
  const [selectedRecommendation, setSelectedRecommendation] = useState<Recommendation | null>(null)
  const [isDetailViewOpen, setIsDetailViewOpen] = useState(false)

  /**
   * 추천사항 로드
   */
  useEffect(() => {
    if (!uuid) {
      setError('Invalid scan UUID')
      setIsLoading(false)
      return
    }

    const loadRecommendations = async () => {
      setIsLoading(true)
      setError(null)

      try {
        const data = await recommendationService.getRecommendations(uuid)
        setRecommendations(data.recommendations)
        setFilteredRecommendations(data.recommendations)
      } catch (err) {
        logError('Failed to load recommendations', err)
        setError('추천사항을 불러오는데 실패했습니다.')
      } finally {
        setIsLoading(false)
      }
    }

    loadRecommendations()
  }, [uuid])

  /**
   * 필터링 로직
   */
  useEffect(() => {
    let filtered = recommendations

    if (algorithmType) {
      filtered = filtered.filter(
        (rec) =>
          rec.targetAlgorithm.toLowerCase().includes(algorithmType.toLowerCase()) ||
          rec.recommendedPQCAlgorithm.toLowerCase().includes(algorithmType.toLowerCase())
      )
    }

    if (context) {
      filtered = filtered.filter((rec) =>
        rec.context.toLowerCase().includes(context.toLowerCase())
      )
    }

    if (priority) {
      filtered = filtered.filter((rec) => rec.priority === priority)
    }

    setFilteredRecommendations(filtered)
  }, [recommendations, algorithmType, context, priority])

  /**
   * 필터 리셋
   */
  const handleResetFilters = () => {
    setAlgorithmType('')
    setContext('')
    setPriority('')
  }

  /**
   * 추천사항 클릭 핸들러
   */
  const handleRecommendationClick = (recommendation: Recommendation) => {
    setSelectedRecommendation(recommendation)
    setIsDetailViewOpen(true)
  }

  /**
   * Detail View 닫기
   */
  const handleCloseDetailView = () => {
    setIsDetailViewOpen(false)
    setSelectedRecommendation(null)
  }

  if (!uuid) {
    return (
      <div className="min-h-screen bg-[#020617] text-white flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 mx-auto mb-4 text-red-400" />
          <p className="text-lg text-slate-300">Invalid scan UUID</p>
          <Link to="/scans/history" className="mt-4 text-indigo-400 hover:text-indigo-300">
            Go back to History
          </Link>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#020617] text-white flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 mx-auto mb-4 text-indigo-400 animate-spin" />
          <p className="text-lg text-slate-300">Loading recommendations...</p>
        </div>
      </div>
    )
  }

  if (error && recommendations.length === 0) {
    return (
      <div className="min-h-screen bg-[#020617] text-white flex items-center justify-center">
        <div className="text-center">
          <XCircle className="w-12 h-12 mx-auto mb-4 text-red-400" />
          <p className="text-lg text-slate-300 mb-4">{error}</p>
          <Link to="/scans/history" className="text-indigo-400 hover:text-indigo-300">
            Go back to History
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#020617] text-white">
      {/* Background Mesh Gradient */}
      <div className="fixed inset-0 bg-gradient-to-br from-slate-900 via-purple-900/20 to-slate-900 pointer-events-none" />
      <div className="fixed inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(99,102,241,0.1),transparent_50%)] pointer-events-none" />

      {/* Main Content */}
      <div className="relative z-10 ml-0 md:ml-64 p-4 md:p-8">
        <div className="max-w-7xl mx-auto space-y-8">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to={`/dashboard/${uuid}`}
                className="p-2 hover:bg-white/10 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-slate-400" />
              </Link>
              <div className="p-3 bg-gradient-to-br from-indigo-500/20 to-purple-600/20 rounded-xl border border-indigo-500/30">
                <Sparkles className="w-6 h-6 text-indigo-400" />
              </div>
              <div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-indigo-400 bg-clip-text text-transparent">
                  PQC Recommendations
                </h1>
                <p className="text-slate-400 text-sm mt-1 font-mono">UUID: {uuid.substring(0, 8)}...</p>
              </div>
            </div>
            {filteredRecommendations.length > 0 && (
              <div className="px-4 py-2 bg-indigo-500/10 border border-indigo-500/30 rounded-full text-sm text-indigo-400">
                {filteredRecommendations.length} recommendation{filteredRecommendations.length !== 1 ? 's' : ''}
              </div>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div
              className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-3 text-red-400"
              role="alert"
            >
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <p className="text-sm">{error}</p>
            </div>
          )}

          {/* Filters */}
          <RecommendationFilters
            algorithmType={algorithmType}
            context={context}
            priority={priority}
            onAlgorithmTypeChange={setAlgorithmType}
            onContextChange={setContext}
            onPriorityChange={setPriority}
            onReset={handleResetFilters}
          />

          {/* Recommendations Table */}
          <RecommendationTable
            recommendations={filteredRecommendations}
            onRecommendationClick={handleRecommendationClick}
          />
        </div>
      </div>

      {/* AI Detail View Modal */}
      <AIDetailView
        recommendation={selectedRecommendation}
        isOpen={isDetailViewOpen}
        onClose={handleCloseDetailView}
      />
    </div>
  )
}
