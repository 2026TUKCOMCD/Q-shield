import { useState, useEffect } from 'react'
import { scanService, type ScanHistoryItem, type ScanStatus } from '../services/scanService'
import { logError } from '../utils/logger'
import {
  RefreshCw,
  ExternalLink,
  CheckCircle2,
  Clock,
  XCircle,
  Loader2,
  Copy,
  Check,
  Eye,
  Trash2,
} from 'lucide-react'
import { Link } from 'react-router-dom'

interface ScanHistoryListProps {
  scans: ScanHistoryItem[]
  onRefresh?: () => void
  onDelete?: (uuid: string) => Promise<void> | void
}

const getStatusConfig = (status: ScanStatus) => {
  switch (status) {
    case 'COMPLETED':
      return {
        icon: CheckCircle2,
        color: 'text-emerald-400',
        bgColor: 'bg-emerald-500/10',
        borderColor: 'border-emerald-500/30',
        label: 'Completed',
      }
    case 'IN_PROGRESS':
      return {
        icon: Loader2,
        color: 'text-blue-400',
        bgColor: 'bg-blue-500/10',
        borderColor: 'border-blue-500/30',
        label: 'In Progress',
      }
    case 'FAILED':
      return {
        icon: XCircle,
        color: 'text-red-400',
        bgColor: 'bg-red-500/10',
        borderColor: 'border-red-500/30',
        label: 'Failed',
      }
    case 'PENDING':
      return {
        icon: Clock,
        color: 'text-yellow-400',
        bgColor: 'bg-yellow-500/10',
        borderColor: 'border-yellow-500/30',
        label: 'Pending',
      }
    default:
      return {
        icon: Clock,
        color: 'text-slate-400',
        bgColor: 'bg-slate-500/10',
        borderColor: 'border-slate-500/30',
        label: status,
      }
  }
}

const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString)
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return dateString
  }
}

const shortenUuid = (uuid: string): string => {
  return `${uuid.substring(0, 8)}...${uuid.substring(uuid.length - 4)}`
}

export const ScanHistoryList = ({ scans, onRefresh, onDelete }: ScanHistoryListProps) => {
  const [refreshingUuids, setRefreshingUuids] = useState<Set<string>>(new Set())
  const [deletingUuids, setDeletingUuids] = useState<Set<string>>(new Set())
  const [copiedUuid, setCopiedUuid] = useState<string | null>(null)

  
  const copyToClipboard = async (uuid: string) => {
    try {
      await navigator.clipboard.writeText(uuid)
      setCopiedUuid(uuid)
      setTimeout(() => setCopiedUuid(null), 2000)
    } catch (error) {
      logError('Failed to copy UUID', error)
    }
  }

  
  const refreshScanStatus = async (uuid: string) => {
    setRefreshingUuids((prev) => new Set(prev).add(uuid))

    try {
      await scanService.getScanStatus(uuid)
      onRefresh?.()
    } catch (error) {
      logError('Failed to refresh scan status', error, { uuid })
    } finally {
      setRefreshingUuids((prev) => {
        const next = new Set(prev)
        next.delete(uuid)
        return next
      })
    }
  }

  const handleDelete = async (uuid: string) => {
    if (!onDelete) {
      return
    }

    const shouldDelete = window.confirm('Delete this scan from history?')
    if (!shouldDelete) {
      return
    }

    setDeletingUuids((prev) => new Set(prev).add(uuid))
    try {
      await onDelete(uuid)
    } catch (error) {
      logError('Failed to delete scan', error, { uuid })
    } finally {
      setDeletingUuids((prev) => {
        const next = new Set(prev)
        next.delete(uuid)
        return next
      })
    }
  }

  useEffect(() => {
    const hasInProgress = scans.some((scan) => scan.status === 'IN_PROGRESS')
    if (!hasInProgress) return

    const interval = setInterval(() => {
      scans.forEach((scan) => {
        if (scan.status === 'IN_PROGRESS') {
          refreshScanStatus(scan.uuid)
        }
      })
    }, 3000)

    return () => clearInterval(interval)
  }, [scans])

  if (scans.length === 0) {
    return (
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-12 text-center">
        <div className="max-w-md mx-auto">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-indigo-500/20 to-purple-600/20 flex items-center justify-center mx-auto mb-4 border border-indigo-500/30">
            <RefreshCw className="w-10 h-10 text-slate-400" />
          </div>
          <p className="text-slate-300 text-lg mb-2 font-medium">No scan history</p>
          <p className="text-slate-500 text-sm">Start a new scan to see results here.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {scans.map((scan) => {
        const statusConfig = getStatusConfig(scan.status)
        const StatusIcon = statusConfig.icon
        const isRefreshing = refreshingUuids.has(scan.uuid)
        const isDeleting = deletingUuids.has(scan.uuid)
        const isCopied = copiedUuid === scan.uuid

        return (
          <div
            key={scan.uuid}
            className="group bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-6 hover:bg-white/10 hover:border-white/20 transition-all duration-300"
          >
            <div className="flex items-start justify-between gap-6">
              <div className="flex-1 min-w-0 space-y-4">
                <div className="flex items-center gap-3 flex-wrap">
                  <div
                    className={`p-2 rounded-lg ${statusConfig.bgColor} ${statusConfig.borderColor} border`}
                  >
                    <StatusIcon
                      className={`w-5 h-5 ${statusConfig.color} ${
                        scan.status === 'IN_PROGRESS' ? 'animate-spin' : ''
                      }`}
                    />
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-semibold ${statusConfig.bgColor} ${statusConfig.borderColor} border ${statusConfig.color}`}
                  >
                    {statusConfig.label}
                  </span>
                  {scan.status === 'IN_PROGRESS' && (
                    <span className="text-sm text-slate-400 font-mono">{scan.progress}%</span>
                  )}
                </div>
                <div>
                  <a
                    href={scan.githubUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-white hover:text-indigo-400 transition-colors flex items-center gap-2 group/link"
                  >
                    <span className="truncate">{scan.githubUrl}</span>
                    <ExternalLink className="w-4 h-4 opacity-0 group-hover/link:opacity-100 transition-opacity flex-shrink-0" />
                  </a>
                </div>
                <div className="flex flex-wrap gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-slate-500">UUID:</span>
                    <span className="font-mono text-xs text-slate-300">{shortenUuid(scan.uuid)}</span>
                    <button
                      onClick={() => copyToClipboard(scan.uuid)}
                      className="p-1 hover:bg-white/10 rounded transition-colors"
                      title="Copy UUID"
                    >
                      {isCopied ? (
                        <Check className="w-3 h-3 text-emerald-400" />
                      ) : (
                        <Copy className="w-3 h-3 text-slate-400" />
                      )}
                    </button>
                  </div>
                  <div>
                    <span className="text-slate-500">Created: </span>
                    <span className="text-slate-300">{formatDate(scan.createdAt)}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Updated: </span>
                    <span className="text-slate-300">{formatDate(scan.updatedAt)}</span>
                  </div>
                </div>
                {scan.status === 'IN_PROGRESS' && (
                  <div className="pt-2">
                    <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full transition-all duration-500"
                        style={{ width: `${scan.progress}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
              <div className="flex items-center gap-2">
                {scan.status === 'COMPLETED' && (
                  <Link
                    to={`/dashboard/${scan.uuid}`}
                    className="px-4 py-2 bg-gradient-to-r from-indigo-500/20 to-purple-600/20 hover:from-indigo-500/30 hover:to-purple-600/30 border border-indigo-500/30 rounded-lg transition-all duration-300 flex items-center gap-2 text-sm text-white"
                  >
                    <Eye className="w-4 h-4" />
                    <span>View Dashboard</span>
                  </Link>
                )}
                <button
                  onClick={() => refreshScanStatus(scan.uuid)}
                  disabled={isRefreshing || isDeleting}
                  className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg transition-all duration-300 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed text-sm text-slate-300 hover:text-white"
                >
                  <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                  <span>Refresh</span>
                </button>
                <button
                  onClick={() => handleDelete(scan.uuid)}
                  disabled={isDeleting || isRefreshing}
                  className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 rounded-lg transition-all duration-300 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed text-sm text-red-300 hover:text-red-200"
                >
                  <Trash2 className={`w-4 h-4 ${isDeleting ? 'animate-pulse' : ''}`} />
                  <span>{isDeleting ? 'Deleting...' : 'Delete'}</span>
                </button>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}


