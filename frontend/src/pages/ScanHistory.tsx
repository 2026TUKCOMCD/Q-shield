import { useEffect, useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import { ScanHistoryList } from '../components/ScanHistoryList'
import { scanService, type ScanHistoryItem } from '../services/scanService'
import { logError } from '../utils/logger'
import { History, Plus, RefreshCw, Search, X, Trash2 } from 'lucide-react'

export const ScanHistory = () => {
  const [scans, setScans] = useState<ScanHistoryItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [queryInput, setQueryInput] = useState('')
  const [activeQuery, setActiveQuery] = useState('')
  const [selectedUuids, setSelectedUuids] = useState<Set<string>>(new Set())
  const [selectionMode, setSelectionMode] = useState(false)
  const [isBulkDeleting, setIsBulkDeleting] = useState(false)
  const scansRef = useRef<ScanHistoryItem[]>([])
  const activeQueryRef = useRef('')

  useEffect(() => {
    scansRef.current = scans
  }, [scans])

  useEffect(() => {
    activeQueryRef.current = activeQuery
  }, [activeQuery])

  const loadScanHistory = async (isInitial: boolean = false, query?: string) => {
    if (isInitial) {
      setIsLoading(true)
    } else {
      setIsRefreshing(true)
    }
    setError(null)

    try {
      const allScans = await scanService.getAllScans(query ?? activeQuery)
      allScans.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
      setScans(allScans)
      setSelectedUuids((prev) => {
        const existing = new Set(allScans.map((s) => s.uuid))
        return new Set([...prev].filter((uuid) => existing.has(uuid)))
      })
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
    loadScanHistory(true, '')

    const interval = setInterval(() => {
      const currentScans = scansRef.current
      const hasInProgress = currentScans.some(
        (scan) => scan.status === 'IN_PROGRESS' || scan.status === 'PENDING'
      )
      if (hasInProgress) {
        loadScanHistory(false, activeQueryRef.current)
      }
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const handleRefresh = () => {
    const current = scansRef.current
    const inProgress = current.filter(
      (scan) => scan.status === 'PENDING' || scan.status === 'IN_PROGRESS'
    )

    Promise.allSettled(inProgress.map((scan) => scanService.getScanStatus(scan.uuid)))
      .catch((err) => {
        logError('Failed to refresh in-progress scans', err)
      })
      .finally(() => {
        loadScanHistory(false, activeQuery)
      })
  }

  const handleSearch = () => {
    const nextQuery = queryInput.trim()
    setActiveQuery(nextQuery)
    loadScanHistory(false, nextQuery)
  }

  const handleClearSearch = () => {
    setQueryInput('')
    setActiveQuery('')
    loadScanHistory(false, '')
  }

  const handleDelete = async (uuid: string) => {
    await scanService.deleteScan(uuid)
    setScans((prev) => prev.filter((scan) => scan.uuid !== uuid))
    setSelectedUuids((prev) => {
      const next = new Set(prev)
      next.delete(uuid)
      return next
    })
  }

  const handleToggleSelect = (uuid: string) => {
    setSelectedUuids((prev) => {
      const next = new Set(prev)
      if (next.has(uuid)) {
        next.delete(uuid)
      } else {
        next.add(uuid)
      }
      return next
    })
  }

  const handleToggleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedUuids(new Set(scans.map((scan) => scan.uuid)))
    } else {
      setSelectedUuids(new Set())
    }
  }

  const handleBulkDelete = async () => {
    if (!selectionMode) {
      setSelectionMode(true)
      return
    }

    if (selectedUuids.size === 0) {
      return
    }
    const shouldDelete = window.confirm(`Delete ${selectedUuids.size} selected scans?`)
    if (!shouldDelete) {
      return
    }

    setIsBulkDeleting(true)
    try {
      const targets = [...selectedUuids]
      await scanService.bulkDeleteScans(targets)
      setScans((prev) => prev.filter((scan) => !selectedUuids.has(scan.uuid)))
      setSelectedUuids(new Set())
      setSelectionMode(false)
    } catch (err) {
      logError('Failed to bulk delete scans', err)
      setError('Failed to delete selected scans.')
    } finally {
      setIsBulkDeleting(false)
    }
  }

  const handleCancelSelection = () => {
    setSelectionMode(false)
    setSelectedUuids(new Set())
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
              <div className="flex items-center gap-2 px-3 py-2 bg-white/5 border border-white/10 rounded-lg min-w-[280px]">
                <Search className="w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  value={queryInput}
                  onChange={(e) => setQueryInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleSearch()
                    }
                  }}
                  placeholder="Search repository URL or name"
                  className="w-full bg-transparent text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none"
                />
                {queryInput && (
                  <button
                    onClick={handleClearSearch}
                    className="p-1 hover:bg-white/10 rounded transition-colors"
                    title="Clear search"
                  >
                    <X className="w-4 h-4 text-slate-400" />
                  </button>
                )}
                <button
                  onClick={handleSearch}
                  className="px-2 py-1 text-xs bg-indigo-500/20 hover:bg-indigo-500/30 border border-indigo-500/30 rounded text-indigo-300"
                >
                  Search
                </button>
              </div>
              <button
                onClick={handleRefresh}
                disabled={isRefreshing || isLoading}
                className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg transition-all duration-300 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed text-slate-300 hover:text-white"
              >
                <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                <span>Refresh</span>
              </button>
              <button
                onClick={handleBulkDelete}
                disabled={isBulkDeleting || (selectionMode && selectedUuids.size === 0)}
                className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 rounded-lg transition-all duration-300 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed text-red-300 hover:text-red-200"
              >
                <Trash2 className={`w-4 h-4 ${isBulkDeleting ? 'animate-pulse' : ''}`} />
                <span>
                  {isBulkDeleting
                    ? 'Deleting...'
                    : selectionMode
                      ? `Delete Selected (${selectedUuids.size})`
                      : 'Delete'}
                </span>
              </button>
              {selectionMode && (
                <button
                  onClick={handleCancelSelection}
                  className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg transition-all duration-300 text-slate-300 hover:text-white"
                >
                  Cancel
                </button>
              )}
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
            <ScanHistoryList
              scans={scans}
              onDelete={handleDelete}
              selectionMode={selectionMode}
              selectedUuids={selectedUuids}
              onToggleSelect={handleToggleSelect}
              onToggleSelectAll={handleToggleSelectAll}
            />
          )}
        </div>
      </div>
    </div>
  )
}
