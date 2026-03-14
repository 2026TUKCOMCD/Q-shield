import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  aiRecommendationService,
  type Recommendation,
  type Priority,
} from '../services/aiRecommendationService'
import { scanService } from '../services/scanService'
import { RecommendationFilters } from '../components/RecommendationFilters'
import { RecommendationTable } from '../components/RecommendationTable'
import { AIDetailView } from '../components/AIDetailView'
import { logError } from '../utils/logger'
import { handleError, ErrorType } from '../utils/errorHandler'
import {
  Loader2,
  AlertCircle,
  ArrowLeft,
  Sparkles,
  XCircle,
} from 'lucide-react'

export const Recommendations = () => {
  const { uuid } = useParams<{ uuid: string }>()

  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [filteredRecommendations, setFilteredRecommendations] = useState<Recommendation[]>([])
  const [scanGithubUrl, setScanGithubUrl] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [algorithmType, setAlgorithmType] = useState('')
  const [priority, setPriority] = useState<Priority | ''>('')

  const [selectedRecommendation, setSelectedRecommendation] = useState<Recommendation | null>(null)
  const [isDetailViewOpen, setIsDetailViewOpen] = useState(false)

  useEffect(() => {
    if (!uuid) {
      setError('Invalid scan UUID')
      setIsLoading(false)
      return
    }

    let isMounted = true

    const loadRecommendations = async () => {
      setIsLoading(true)
      setError(null)

      try {
        const data = await aiRecommendationService.getRecommendations(uuid)
        if (isMounted) {
          setRecommendations(data.recommendations)
          setFilteredRecommendations(data.recommendations)
        }
      } catch (err) {
        logError('Failed to load recommendations', err)
        if (isMounted) {
          const appError = handleError(err)
          if (appError.type === ErrorType.API_ERROR && appError.statusCode === 202) {
            setError(appError.message)
          } else {
            setError('Failed to load AI recommendations.')
          }
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    const loadScanMetadata = async () => {
      try {
        const scanStatus = await scanService.getScanStatus(uuid)
        if (isMounted) {
          setScanGithubUrl(scanStatus.githubUrl ?? null)
        }
      } catch (err) {
        logError('Failed to load scan metadata', err)
      }
    }

    void loadRecommendations()
    void loadScanMetadata()

    return () => {
      isMounted = false
    }
  }, [uuid])

  useEffect(() => {
    let filtered = recommendations

    if (algorithmType) {
      const tokens = algorithmType
        .split(',')
        .map((token) => token.trim().toLowerCase())
        .filter(Boolean)

      if (tokens.length > 0) {
        filtered = filtered.filter((rec) => {
          const targetAlgorithm = rec.targetAlgorithm.toLowerCase()
          return tokens.some((token) => targetAlgorithm.includes(token))
        })
      }
    }

    if (priority) {
      filtered = filtered.filter((rec) => rec.priority === priority)
    }

    setFilteredRecommendations(filtered)
  }, [recommendations, algorithmType, priority])

  const handleResetFilters = () => {
    setAlgorithmType('')
    setPriority('')
  }

  const handleRecommendationClick = (recommendation: Recommendation) => {
    setSelectedRecommendation(recommendation)
    setIsDetailViewOpen(true)
  }

  const handleCloseDetailView = () => {
    setIsDetailViewOpen(false)
    setSelectedRecommendation(null)
  }

  const handleRetryCitations = async () => {
    if (!uuid || !selectedRecommendation) {
      return
    }

    const data = await aiRecommendationService.getRecommendations(uuid, undefined, {
      forceAnalysisRefresh: true,
    })
    setRecommendations(data.recommendations)
    setError(null)

    const refreshedRecommendation =
      data.recommendations.find((recommendation) => recommendation.id === selectedRecommendation.id) ??
      data.recommendations.find(
        (recommendation) => recommendation.issueName === selectedRecommendation.issueName,
      ) ??
      selectedRecommendation

    setSelectedRecommendation(refreshedRecommendation)
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
          <p className="text-lg text-slate-300">Generating AI recommendations...</p>
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
      <div className="fixed inset-0 bg-gradient-to-br from-slate-900 via-purple-900/20 to-slate-900 pointer-events-none" />
      <div className="fixed inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(99,102,241,0.1),transparent_50%)] pointer-events-none" />
      <div className="relative z-10 ml-0 md:ml-64 p-4 md:p-8">
        <div className="max-w-7xl mx-auto space-y-8">
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
                {scanGithubUrl ? (
                  <a
                    href={scanGithubUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-indigo-300 text-sm mt-1 font-mono hover:text-indigo-200 hover:underline break-all inline-block"
                  >
                    {scanGithubUrl}
                  </a>
                ) : (
                  <p className="text-slate-400 text-sm mt-1 font-mono">
                    UUID: {uuid.substring(0, 8)}...
                  </p>
                )}
              </div>
            </div>
            {filteredRecommendations.length > 0 && (
              <div className="px-4 py-2 bg-indigo-500/10 border border-indigo-500/30 rounded-full text-sm text-indigo-400">
                {filteredRecommendations.length} recommendation{filteredRecommendations.length !== 1 ? 's' : ''}
              </div>
            )}
          </div>

          {error && (
            <div
              className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-3 text-red-400"
              role="alert"
            >
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <p className="text-sm">{error}</p>
            </div>
          )}

          <RecommendationFilters
            algorithmType={algorithmType}
            priority={priority}
            onAlgorithmTypeChange={setAlgorithmType}
            onPriorityChange={setPriority}
            onReset={handleResetFilters}
          />

          <RecommendationTable
            recommendations={filteredRecommendations}
            onRecommendationClick={handleRecommendationClick}
          />
        </div>
      </div>

      <AIDetailView
        recommendation={selectedRecommendation}
        isOpen={isDetailViewOpen}
        onClose={handleCloseDetailView}
        onRetryCitations={handleRetryCitations}
      />
    </div>
  )
}
