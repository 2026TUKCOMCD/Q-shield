import { useEffect, useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import { ScanHistoryList } from '../components/ScanHistoryList'
import { scanService, type ScanHistoryItem } from '../services/scanService'
import { logError } from '../utils/logger'
import { History, Plus, RefreshCw } from 'lucide-react'

export const ScanHistory = () => {
  const [scans, setScans] = useState<ScanHistoryItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const scansRef = useRef<ScanHistoryItem[]>([])

  useEffect(() => {
    scansRef.current = scans
  }, [scans])

  const loadScanHistory = async (isInitial: boolean = false) => {
    if (isInitial) {
      setIsLoading(true)
    } else {
      setIsRefreshing(true)
    }
    setError(null)

    try {
      const allScans = await scanService.getAllScans()
      allScans.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
      setScans(allScans)
    } catch (err) {
      logError('Failed to load scan history', err)
      setError('Failed to load scan history.')
    } finally {
      if (isInitial) {
        setIsLoading(false)
      } else {
        setIsRefreshing(false)
      }
    }
  }

  useEffect(() => {
    loadScanHistory(true)

    const interval = setInterval(() => {
      const currentScans = scansRef.current
      const hasInProgress = currentScans.some((scan) => scan.status === 'IN_PROGRESS')
      if (hasInProgress) {
        loadScanHistory(false)
      }
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const handleRefresh = () => {
    loadScanHistory(false)
  }

  return (
    <div className="min-h-screen bg-[#020617] text-white">
      <div className="fixed inset-0 bg-gradient-to-br from-slate-900 via-purple-900/20 to-slate-900 pointer-events-none" />
      <div className="fixed inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(99,102,241,0.1),transparent_50%)] pointer-events-none" />
      <div className="relative z-10 ml-0 md:ml-64 p-4 md:p-8">
        <div className="max-w-6xl mx-auto space-y-8">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gradient-to-br from-indigo-500/20 to-purple-600/20 rounded-xl border border-indigo-500/30">
                <History className="w-6 h-6 text-indigo-400" />
              </div>
              <div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-indigo-400 bg-clip-text text-transparent">
                  Scan History
                </h1>
                <p className="text-slate-400 text-sm mt-1">
                  {scans.length} {scans.length === 1 ? 'scan' : 'scans'} total
                </p>
              </div>
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleRefresh}
                disabled={isRefreshing || isLoading}
                className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg transition-all duration-300 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed text-slate-300 hover:text-white"
              >
                <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                <span>Refresh</span>
              </button>
              <Link
                to="/scans/new"
                className="px-6 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl hover:shadow-purple-500/25 transition-all duration-300 flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                <span>New Scan</span>
              </Link>
            </div>
          </div>

          {error && (
            <div
              className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-3 text-red-400"
              role="alert"
            >
              <p className="text-sm">{error}</p>
            </div>
          )}

          {isLoading ? (
            <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-12 text-center">
              <RefreshCw className="w-12 h-12 animate-spin mx-auto mb-4 text-indigo-400" />
              <p className="text-slate-300 text-lg">Loading...</p>
            </div>
          ) : (
            <ScanHistoryList scans={scans} onRefresh={handleRefresh} />
          )}
        </div>
      </div>
    </div>
  )
}
