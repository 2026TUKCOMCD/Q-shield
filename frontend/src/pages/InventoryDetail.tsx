import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { inventoryService, type AssetDetail } from '../services/inventoryService'
import { type AppError } from '../utils/errorHandler'
import { AssetDetailList } from '../components/AssetDetailList'
import { logError } from '../utils/logger'
import {
  Loader2,
  AlertCircle,
  ArrowLeft,
  Shield,
  XCircle,
  AlertTriangle,
  CheckCircle2,
} from 'lucide-react'

const getRiskConfig = (riskScore: number) => {
  if (riskScore >= 8.0) {
    return {
      color: 'text-red-400',
      bg: 'bg-red-500/10',
      border: 'border-red-500/30',
      label: 'Critical',
      icon: AlertCircle,
    }
  }
  if (riskScore >= 5.0) {
    return {
      color: 'text-orange-400',
      bg: 'bg-orange-500/10',
      border: 'border-orange-500/30',
      label: 'High',
      icon: AlertTriangle,
    }
  }
  return {
    color: 'text-yellow-400',
    bg: 'bg-yellow-500/10',
    border: 'border-yellow-500/30',
    label: 'Medium',
    icon: CheckCircle2,
  }
}

export const InventoryDetail = () => {
  const { uuid, assetId } = useParams<{ uuid: string; assetId: string }>()

  const [asset, setAsset] = useState<AssetDetail | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  
  useEffect(() => {
    if (!uuid || !assetId) {
      setError('Invalid scan UUID or asset ID')
      setIsLoading(false)
      return
    }

    const loadAssetDetail = async () => {
      setIsLoading(true)
      setError(null)

      try {
        const data = await inventoryService.getAssetDetail(uuid, assetId)
        setAsset(data)
      } catch (err) {
        const appError = err as AppError
        logError('Failed to load asset detail', err)
        if (appError?.statusCode === 404) {
          setError('Asset not found.')
        } else {
          setError('자산 상세 정보를 불러오는데 실패했습니다.')
        }
      } finally {
        setIsLoading(false)
      }
    }

    loadAssetDetail()
  }, [uuid, assetId])

  if (!uuid || !assetId) {
    return (
      <div className="min-h-screen bg-[#020617] text-white flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 mx-auto mb-4 text-red-400" />
          <p className="text-lg text-slate-300">Invalid scan UUID or asset ID</p>
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
          <p className="text-lg text-slate-300">Loading asset details...</p>
        </div>
      </div>
    )
  }

  if (error && !asset) {
    return (
      <div className="min-h-screen bg-[#020617] text-white flex items-center justify-center">
        <div className="text-center">
          <XCircle className="w-12 h-12 mx-auto mb-4 text-red-400" />
          <p className="text-lg text-slate-300 mb-4">{error}</p>
          <Link to={`/dashboard/${uuid}`} className="text-indigo-400 hover:text-indigo-300">
            Go back to Dashboard
          </Link>
        </div>
      </div>
    )
  }

  if (!asset) {
    return null
  }

  const riskConfig = getRiskConfig(asset.riskScore)
  const RiskIcon = riskConfig.icon

  return (
    <div className="min-h-screen bg-[#020617] text-white">
      <div className="fixed inset-0 bg-gradient-to-br from-slate-900 via-purple-900/20 to-slate-900 pointer-events-none" />
      <div className="fixed inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(99,102,241,0.1),transparent_50%)] pointer-events-none" />
      <div className="relative z-10 ml-0 md:ml-64 p-4 md:p-8">
        <div className="max-w-5xl mx-auto space-y-8">
          <div className="flex items-center gap-4">
            <Link
              to={`/dashboard/${uuid}`}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-slate-400" />
            </Link>
            <div className="p-3 bg-gradient-to-br from-indigo-500/20 to-purple-600/20 rounded-xl border border-indigo-500/30">
              <Shield className="w-6 h-6 text-indigo-400" />
            </div>
            <div className="flex-1">
              <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-indigo-400 bg-clip-text text-transparent">
                Asset Details
              </h1>
              <p className="text-slate-400 text-sm mt-1 font-mono">UUID: {uuid.substring(0, 8)}...</p>
            </div>
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
          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-8">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
              <div className="flex-1">
                <div className="flex items-center gap-4 mb-4">
                  <div className="p-3 bg-gradient-to-br from-indigo-500/20 to-purple-600/20 rounded-xl border border-indigo-500/30">
                    <Shield className="w-8 h-8 text-indigo-400" />
                  </div>
                  <div>
                    <h2 className="text-3xl font-bold text-white mb-2">{asset.algorithmType}</h2>
                    <p className="text-slate-400 text-sm">Cryptographic Asset Analysis</p>
                  </div>
                </div>
              </div>
              <div
                className={`px-6 py-4 rounded-xl ${riskConfig.bg} ${riskConfig.border} border flex items-center gap-3`}
              >
                <RiskIcon className={`w-6 h-6 ${riskConfig.color}`} />
                <div>
                  <div className={`text-sm ${riskConfig.color} opacity-70`}>Risk Level</div>
                  <div className={`text-2xl font-bold ${riskConfig.color}`}>
                    {asset.riskScore.toFixed(1)}
                  </div>
                  <div className={`text-xs ${riskConfig.color} opacity-70`}>
                    {riskConfig.label}
                  </div>
                </div>
              </div>
            </div>
          </div>
          <AssetDetailList asset={asset} />
          <div className="flex justify-center">
            <Link
              to={`/dashboard/${uuid}`}
              className="px-6 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg transition-all duration-300 flex items-center gap-2 text-slate-300 hover:text-white"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Dashboard</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}


