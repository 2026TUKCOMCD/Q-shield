import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  inferAssetLocationScope,
  inferInventorySignals,
  type CryptographicAsset,
} from '../services/inventoryService'
import {
  FileCode,
  AlertCircle,
  CheckCircle2,
  AlertTriangle,
  Search,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'

interface InventoryTableProps {
  inventory: CryptographicAsset[]
  scanUuid?: string
}

const PAGE_SIZE = 25

const getRiskColor = (riskScore: number) => {
  if (riskScore >= 8.0)
    return { color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30', label: 'High' }
  if (riskScore >= 5.0)
    return {
      color: 'text-orange-400',
      bg: 'bg-orange-500/10',
      border: 'border-orange-500/30',
      label: 'Medium',
    }
  return {
    color: 'text-yellow-400',
    bg: 'bg-yellow-500/10',
    border: 'border-yellow-500/30',
    label: 'Low',
  }
}

const getRiskIcon = (riskScore: number) => {
  if (riskScore >= 8.0) return AlertCircle
  if (riskScore >= 5.0) return AlertTriangle
  return CheckCircle2
}

const truncatePath = (value: string, limit: number) => {
  if (value.length <= limit) {
    return value
  }
  return `${value.slice(0, limit - 1)}...`
}

export const InventoryTable = ({ inventory, scanUuid }: InventoryTableProps) => {
  const navigate = useNavigate()
  const [searchTerm, setSearchTerm] = useState('')
  const [riskFilter, setRiskFilter] = useState<'ALL' | 'HIGH' | 'MEDIUM' | 'LOW'>('ALL')
  const [familyFilter, setFamilyFilter] = useState('ALL')
  const [page, setPage] = useState(1)

  const handleRowClick = (assetId: string) => {
    if (scanUuid) {
      navigate(`/scans/${scanUuid}/inventory/${encodeURIComponent(assetId)}`)
    }
  }

  const search = searchTerm.trim().toLowerCase()
  const familyOptions = Array.from(
    new Set(
      inventory
        .map((asset) => asset.algorithmFamily)
        .filter((family): family is string => Boolean(family && family.trim())),
    ),
  ).sort((left, right) => left.localeCompare(right))

  const filteredInventory = inventory.filter((asset) => {
    const riskLabel = asset.riskScore >= 8.0 ? 'HIGH' : asset.riskScore >= 5.0 ? 'MEDIUM' : 'LOW'
    const matchesRisk = riskFilter === 'ALL' || riskFilter === riskLabel
    const matchesFamily = familyFilter === 'ALL' || asset.algorithmFamily === familyFilter
    const matchesSearch =
      !search ||
      [
        asset.algorithmType,
        asset.filePath,
        asset.assetRef,
        asset.correlationRef,
        asset.algorithmFamily,
      ]
        .filter((value): value is string => Boolean(value))
        .some((value) => value.toLowerCase().includes(search))

    return matchesRisk && matchesFamily && matchesSearch
  })

  const totalPages = Math.max(1, Math.ceil(filteredInventory.length / PAGE_SIZE))
  const safePage = Math.min(page, totalPages)
  const pagedInventory = filteredInventory.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE)

  const setNextPage = (nextPage: number) => {
    setPage(Math.max(1, Math.min(totalPages, nextPage)))
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
      <div className="border-b border-white/10 p-4 md:p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-medium text-indigo-300">
                Showing {filteredInventory.length} of {inventory.length}
              </span>
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300">
                Page {safePage} / {totalPages}
              </span>
            </div>
            <p className="mt-3 text-sm text-slate-400">
              Use the table for triage. Open a row to inspect full correlation identifiers and detailed evidence.
            </p>
          </div>

          <div className="grid w-full gap-3 md:grid-cols-3 lg:w-auto lg:min-w-[760px]">
            <label className="relative block">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
              <input
                value={searchTerm}
                onChange={(event) => {
                  setSearchTerm(event.target.value)
                  setPage(1)
                }}
                placeholder="Search file path, family, ref"
                className="w-full rounded-lg border border-white/10 bg-white/5 py-2.5 pl-10 pr-3 text-sm text-white placeholder:text-slate-500 focus:border-indigo-400/50 focus:outline-none"
              />
            </label>

            <select
              value={familyFilter}
              onChange={(event) => {
                setFamilyFilter(event.target.value)
                setPage(1)
              }}
              className="rounded-lg border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white focus:border-indigo-400/50 focus:outline-none"
            >
              <option value="ALL">All families</option>
              {familyOptions.map((family) => (
                <option key={family} value={family}>
                  {family}
                </option>
              ))}
            </select>

            <select
              value={riskFilter}
              onChange={(event) => {
                setRiskFilter(event.target.value as 'ALL' | 'HIGH' | 'MEDIUM' | 'LOW')
                setPage(1)
              }}
              className="rounded-lg border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white focus:border-indigo-400/50 focus:outline-none"
            >
              <option value="ALL">All risk levels</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>
        </div>
      </div>

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
            {pagedInventory.map((asset) => {
              const riskConfig = getRiskColor(asset.riskScore)
              const RiskIcon = getRiskIcon(asset.riskScore)
              const signals = inferInventorySignals(asset)
              const locationScope = inferAssetLocationScope(asset)

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
                    <div className="mt-2 flex flex-wrap gap-2">
                      <span className="rounded-full border border-indigo-400/20 bg-indigo-500/10 px-2.5 py-1 text-[11px] text-indigo-300">
                        {signals.classLabel}
                      </span>
                    </div>
                    <p className="mt-2 max-w-xs text-xs leading-relaxed text-slate-400">
                      {signals.classReason}
                    </p>
                  </td>
                  <td className="px-6 py-4">
                    <code
                      title={asset.filePath}
                      className="inline-block max-w-[520px] truncate align-middle rounded bg-white/5 px-2 py-1 font-mono text-sm text-slate-300"
                    >
                      {truncatePath(asset.filePath, 72)}
                    </code>
                    <div className="mt-2 flex flex-wrap gap-2">
                      <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[11px] text-slate-300">
                        {signals.boundaryLabel}
                      </span>
                      {asset.algorithmFamily && (
                        <span className="rounded-full border border-emerald-400/20 bg-emerald-500/10 px-2.5 py-1 text-[11px] uppercase tracking-[0.14em] text-emerald-300">
                          {asset.algorithmFamily}
                        </span>
                      )}
                      {scanUuid && (
                        <span className="rounded-full border border-indigo-400/20 bg-indigo-500/10 px-2.5 py-1 text-[11px] text-indigo-300">
                          View details
                        </span>
                      )}
                    </div>
                    <p className="mt-2 text-xs text-slate-400">
                      {asset.lineNumbers.length > 0
                        ? `Line-level evidence across ${asset.lineNumbers.length} hit${
                            asset.lineNumbers.length > 1 ? 's' : ''
                          }`
                        : `${locationScope} evidence`}
                    </p>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {asset.lineNumbers.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {asset.lineNumbers.slice(0, 8).map((line, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 text-xs bg-white/5 text-slate-300 rounded font-mono"
                          >
                            {line}
                          </span>
                        ))}
                        {asset.lineNumbers.length > 8 && (
                          <span className="px-2 py-1 text-xs bg-indigo-500/10 text-indigo-300 rounded font-mono">
                            +{asset.lineNumbers.length - 8} more
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="inline-flex rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[11px] uppercase tracking-[0.12em] text-slate-300">
                        {locationScope}
                      </span>
                    )}
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
                    <p className="mt-2 text-xs text-slate-400">{signals.trustLabel}</p>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {filteredInventory.length > 0 && (
        <div className="flex flex-col gap-3 border-t border-white/10 px-4 py-4 md:flex-row md:items-center md:justify-between">
          <p className="text-sm text-slate-400">
            Showing rows {(safePage - 1) * PAGE_SIZE + 1}-{Math.min(safePage * PAGE_SIZE, filteredInventory.length)}
          </p>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setNextPage(safePage - 1)}
              disabled={safePage === 1}
              className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <ChevronLeft className="h-4 w-4" />
              Prev
            </button>
            <button
              type="button"
              onClick={() => setNextPage(safePage + 1)}
              disabled={safePage === totalPages}
              className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
