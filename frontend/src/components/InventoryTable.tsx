import { useNavigate } from 'react-router-dom'
import { type CryptographicAsset } from '../services/inventoryService'
import { FileCode, AlertCircle, CheckCircle2, AlertTriangle } from 'lucide-react'

interface InventoryTableProps {
  inventory: CryptographicAsset[]
  scanUuid?: string
}

const getRiskColor = (riskScore: number) => {
  if (riskScore >= 8.0) return { color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30', label: 'High' }
  if (riskScore >= 5.0) return { color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/30', label: 'Medium' }
  return { color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', label: 'Low' }
}

const getRiskIcon = (riskScore: number) => {
  if (riskScore >= 8.0) return AlertCircle
  if (riskScore >= 5.0) return AlertTriangle
  return CheckCircle2
}

export const InventoryTable = ({ inventory, scanUuid }: InventoryTableProps) => {
  const navigate = useNavigate()

  const handleRowClick = (assetId: string) => {
    if (scanUuid) {
      navigate(`/scans/${scanUuid}/inventory/${assetId}`)
    }
  }

  if (inventory.length === 0) {
    return (
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-12 text-center">
        <FileCode className="w-12 h-12 mx-auto mb-4 text-slate-400" />
        <p className="text-slate-300 text-lg mb-2 font-medium">No cryptographic assets found</p>
        <p className="text-slate-500 text-sm">The scan did not detect any cryptographic assets.</p>
      </div>
    )
  }

  return (
    <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/10">
              <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Algorithm Type
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                File Path
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Line Numbers
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Risk Score
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {inventory.map((asset) => {
              const riskConfig = getRiskColor(asset.riskScore)
              const RiskIcon = getRiskIcon(asset.riskScore)

              return (
                <tr
                  key={asset.id}
                  onClick={() => scanUuid && handleRowClick(asset.id)}
                  className={`hover:bg-white/5 transition-colors duration-200 ${
                    scanUuid ? 'cursor-pointer' : ''
                  }`}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 bg-indigo-500/10 rounded border border-indigo-500/20">
                        <FileCode className="w-4 h-4 text-indigo-400" />
                      </div>
                      <span className="text-white font-medium">{asset.algorithmType}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <code className="text-sm text-slate-300 font-mono bg-white/5 px-2 py-1 rounded">
                      {asset.filePath}
                    </code>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex flex-wrap gap-1">
                      {asset.lineNumbers.map((line, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 text-xs bg-white/5 text-slate-300 rounded font-mono"
                        >
                          {line}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <div
                        className={`px-3 py-1.5 rounded-lg ${riskConfig.bg} ${riskConfig.border} border flex items-center gap-2`}
                      >
                        <RiskIcon className={`w-4 h-4 ${riskConfig.color}`} />
                        <span className={`text-sm font-semibold ${riskConfig.color}`}>
                          {asset.riskScore.toFixed(1)}
                        </span>
                        <span className={`text-xs ${riskConfig.color} opacity-70`}>
                          {riskConfig.label}
                        </span>
                      </div>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}


