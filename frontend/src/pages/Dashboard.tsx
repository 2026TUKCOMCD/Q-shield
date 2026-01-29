import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { scanService, type ScanStatusResponse } from '../services/scanService'
import { inventoryService, type InventoryResponse } from '../services/inventoryService'
import { PqcReadinessGauge } from '../components/PqcReadinessGauge'
import { InventoryTable } from '../components/InventoryTable'
import { logError } from '../utils/logger'
import {
  Loader2,
  AlertCircle,
  CheckCircle2,
  XCircle,
  ArrowLeft,
  Activity,
  Shield,
  Sparkles,
} from 'lucide-react'

/**
 * Dashboard 페이지
 * T012: 실시간 스캔 진행 상황 및 PQC 준비도 대시보드
 */
export const Dashboard = () => {
  const { uuid } = useParams<{ uuid: string }>()
  const navigate = useNavigate()

  const [scanStatus, setScanStatus] = useState<ScanStatusResponse | null>(null)
  const [inventory, setInventory] = useState<InventoryResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  /**
   * 스캔 상태 폴링 (2초마다)
   */
  useEffect(() => {
    if (!uuid) {
      setError('Invalid scan UUID')
      setIsLoading(false)
      return
    }

    let pollingInterval: NodeJS.Timeout | null = null
    let isMounted = true

    const pollScanStatus = async () => {
      try {
        const status = await scanService.getScanStatus(uuid)
        if (!isMounted) return

        setScanStatus(status)
        setIsLoading(false)

        // 스캔이 완료되면 인벤토리 데이터 가져오기
        if (status.status === 'COMPLETED' && !inventory) {
          try {
            const inventoryData = await inventoryService.getScanInventory(uuid)
            if (isMounted) {
              setInventory(inventoryData)
            }
          } catch (err) {
            logError('Failed to load inventory', err)
          }
        }

        // 스캔이 완료되거나 실패하면 폴링 중지
        if (status.status === 'COMPLETED' || status.status === 'FAILED') {
          if (pollingInterval) {
            clearInterval(pollingInterval)
            pollingInterval = null
          }
        }
      } catch (err) {
        if (isMounted) {
          logError('Failed to poll scan status', err)
          setError('스캔 상태를 불러오는데 실패했습니다.')
          setIsLoading(false)
        }
      }
    }

    // 즉시 한 번 실행
    pollScanStatus()

    // 1초마다 폴링 (데모용 빠른 업데이트)
    pollingInterval = setInterval(pollScanStatus, 1000)

    return () => {
      isMounted = false
      if (pollingInterval) {
        clearInterval(pollingInterval)
      }
    }
  }, [uuid, inventory])

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

  if (isLoading && !scanStatus) {
    return (
      <div className="min-h-screen bg-[#020617] text-white flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 mx-auto mb-4 text-indigo-400 animate-spin" />
          <p className="text-lg text-slate-300">Loading scan status...</p>
        </div>
      </div>
    )
  }

  if (error && !scanStatus) {
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

  const isScanning = scanStatus?.status === 'PENDING' || scanStatus?.status === 'IN_PROGRESS'
  const isCompleted = scanStatus?.status === 'COMPLETED'
  const isFailed = scanStatus?.status === 'FAILED'

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
                to="/scans/history"
                className="p-2 hover:bg-white/10 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-slate-400" />
              </Link>
              <div className="p-3 bg-gradient-to-br from-indigo-500/20 to-purple-600/20 rounded-xl border border-indigo-500/30">
                <Activity className="w-6 h-6 text-indigo-400" />
              </div>
              <div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-indigo-400 bg-clip-text text-transparent">
                  Scan Dashboard
                </h1>
                <p className="text-slate-400 text-sm mt-1 font-mono">UUID: {uuid.substring(0, 8)}...</p>
              </div>
            </div>
          </div>

          {/* Scanning State */}
          {isScanning && scanStatus && (
            <div className="space-y-6 animate-in fade-in duration-500">
              {/* Status Card */}
              <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-8">
                <div className="flex items-center gap-4 mb-6">
                  <div className="p-3 bg-blue-500/10 rounded-xl border border-blue-500/30">
                    <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-semibold text-white">Scanning in Progress</h2>
                    <p className="text-sm text-slate-400 mt-1">
                      {scanStatus.status === 'PENDING' ? 'Preparing scan...' : 'Analyzing repository...'}
                    </p>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-300">Progress</span>
                    <span className="text-white font-semibold">{scanStatus.progress}%</span>
                  </div>
                  <div className="h-4 bg-white/5 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full transition-all duration-500"
                      style={{ width: `${scanStatus.progress}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Info Message */}
              <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4 flex items-start gap-3">
                <Activity className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm text-blue-300 font-medium">Scan is running</p>
                  <p className="text-xs text-blue-400/70 mt-1">
                    This page will automatically update when the scan completes.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Failed State */}
          {isFailed && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-8 text-center">
              <XCircle className="w-12 h-12 mx-auto mb-4 text-red-400" />
              <h2 className="text-2xl font-semibold text-white mb-2">Scan Failed</h2>
              <p className="text-slate-400 mb-6">The scan encountered an error and could not complete.</p>
              <Link
                to="/scans/new"
                className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-semibold rounded-lg transition-all duration-300"
              >
                Start New Scan
              </Link>
            </div>
          )}

          {/* Result State */}
          {isCompleted && inventory && (
            <div className="space-y-8 animate-in fade-in duration-500">
              {/* PQC Readiness Gauge */}
              <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-8">
                <div className="flex items-center gap-3 mb-6">
                  <div className="p-2 bg-gradient-to-br from-indigo-500/20 to-purple-600/20 rounded-lg border border-indigo-500/30">
                    <Shield className="w-5 h-5 text-indigo-400" />
                  </div>
                  <h2 className="text-2xl font-semibold text-white">PQC Readiness Score</h2>
                </div>
                <PqcReadinessGauge score={inventory.pqcReadinessScore} />
              </div>

              {/* Algorithm Ratios */}
              {Object.keys(inventory.algorithmRatios).length > 0 && (
                <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Algorithm Distribution</h3>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    {Object.entries(inventory.algorithmRatios).map(([algorithm, ratio]) => (
                      <div
                        key={algorithm}
                        className="bg-white/5 rounded-lg p-4 border border-white/10 text-center"
                      >
                        <div className="text-2xl font-bold text-white mb-1">
                          {(ratio * 100).toFixed(0)}%
                        </div>
                        <div className="text-xs text-slate-400">{algorithm}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Inventory Table */}
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <h2 className="text-2xl font-semibold text-white">Cryptographic Assets</h2>
                  <span className="px-3 py-1 bg-indigo-500/10 border border-indigo-500/30 rounded-full text-sm text-indigo-400">
                    {inventory.inventory.length} items
                  </span>
                </div>
                <InventoryTable inventory={inventory.inventory} />
              </div>

              {/* Recommendations Link */}
              <div className="bg-gradient-to-r from-indigo-500/10 to-purple-600/10 border border-indigo-500/30 rounded-xl p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-gradient-to-br from-indigo-500/20 to-purple-600/20 rounded-xl border border-indigo-500/30">
                      <Sparkles className="w-6 h-6 text-indigo-400" />
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold text-white mb-1">View PQC Recommendations</h3>
                      <p className="text-sm text-slate-400">
                        Get AI-powered migration guides for post-quantum cryptography
                      </p>
                    </div>
                  </div>
                  <Link
                    to={`/scans/${uuid}/recommendations`}
                    className="px-6 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl hover:shadow-purple-500/25 transition-all duration-300 flex items-center gap-2"
                  >
                    <Sparkles className="w-4 h-4" />
                    View Recommendations
                  </Link>
                </div>
              </div>
            </div>
          )}

          {/* Loading Inventory State */}
          {isCompleted && !inventory && (
            <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-12 text-center">
              <Loader2 className="w-12 h-12 mx-auto mb-4 text-indigo-400 animate-spin" />
              <p className="text-slate-300 text-lg">Loading inventory data...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
