import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { heatmapService, type HeatmapResponse } from '../services/heatmapService'
import { FileTree } from '../components/FileTree'
import { logError } from '../utils/logger'
import {
  Loader2,
  AlertCircle,
  ArrowLeft,
  Map,
  XCircle,
  AlertTriangle,
  Info,
  CheckCircle2,
} from 'lucide-react'

/**
 * RepositoryHeatmap 페이지
 * T021: 리포지토리 리스크 분포 히트맵 시각화
 */
export const RepositoryHeatmap = () => {
  const { uuid } = useParams<{ uuid: string }>()
  const navigate = useNavigate()

  const [heatmapData, setHeatmapData] = useState<HeatmapResponse>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  /**
   * 히트맵 데이터 로드
   */
  useEffect(() => {
    if (!uuid) {
      setError('Invalid scan UUID')
      setIsLoading(false)
      return
    }

    const loadHeatmap = async () => {
      setIsLoading(true)
      setError(null)

      try {
        const data = await heatmapService.getHeatmap(uuid)
        setHeatmapData(data)
      } catch (err) {
        logError('Failed to load heatmap', err)
        setError('히트맵 데이터를 불러오는데 실패했습니다.')
      } finally {
        setIsLoading(false)
      }
    }

    loadHeatmap()
  }, [uuid])

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
          <p className="text-lg text-slate-300">Loading repository heatmap...</p>
        </div>
      </div>
    )
  }

  if (error && heatmapData.length === 0) {
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
                <Map className="w-6 h-6 text-indigo-400" />
              </div>
              <div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-indigo-400 bg-clip-text text-transparent">
                  Repository Heatmap
                </h1>
                <p className="text-slate-400 text-sm mt-1 font-mono">UUID: {uuid.substring(0, 8)}...</p>
              </div>
            </div>
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

          {/* Legend */}
          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Risk Level Legend</h2>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="flex items-center gap-3">
                <div className="w-4 h-4 rounded bg-red-500/20 border border-red-500/50" />
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-red-400" />
                  <span className="text-sm text-slate-300">Critical (≥8.0)</span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-4 h-4 rounded bg-orange-500/20 border border-orange-500/50" />
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-orange-400" />
                  <span className="text-sm text-slate-300">High (≥5.0)</span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-4 h-4 rounded bg-yellow-500/20 border border-yellow-500/50" />
                <div className="flex items-center gap-2">
                  <Info className="w-4 h-4 text-yellow-400" />
                  <span className="text-sm text-slate-300">Medium (≥3.0)</span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-4 h-4 rounded bg-blue-500/20 border border-blue-500/50" />
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-blue-400" />
                  <span className="text-sm text-slate-300">Low (&gt;0)</span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-4 h-4 rounded bg-slate-500/20 border border-slate-500/30" />
                <span className="text-sm text-slate-400">Safe (0.0)</span>
              </div>
            </div>
            <p className="text-xs text-slate-500 mt-4">
              Folders display the highest risk level found within their children. Click folders to
              expand/collapse.
            </p>
          </div>

          {/* File Tree */}
          <FileTree data={heatmapData} />
        </div>
      </div>
    </div>
  )
}
