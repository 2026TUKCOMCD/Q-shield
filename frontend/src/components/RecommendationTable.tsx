import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  FileCode,
  Info,
  Sparkles,
} from 'lucide-react'

import { type Priority, type Recommendation } from '../services/aiRecommendationService'

interface RecommendationTableProps {
  recommendations: Recommendation[]
  onRecommendationClick: (recommendation: Recommendation) => void
}

const hasDisplayValue = (value?: string | null): value is string => {
  if (!value) {
    return false
  }

  const normalizedValue = value.trim()
  return normalizedValue !== '' && normalizedValue.toUpperCase() !== 'N/A'
}

const getDisplayValue = (
  value?: string | null,
  fallback = 'Not available',
) => (hasDisplayValue(value) ? value.trim() : fallback)

const getPriorityConfig = (priority: Priority) => {
  switch (priority) {
    case 'CRITICAL':
      return {
        color: 'text-red-400',
        bg: 'bg-red-500/10',
        border: 'border-red-500/30',
        label: 'Critical',
        icon: AlertCircle,
      }
    case 'HIGH':
      return {
        color: 'text-orange-400',
        bg: 'bg-orange-500/10',
        border: 'border-orange-500/30',
        label: 'High',
        icon: AlertTriangle,
      }
    case 'MEDIUM':
      return {
        color: 'text-yellow-400',
        bg: 'bg-yellow-500/10',
        border: 'border-yellow-500/30',
        label: 'Medium',
        icon: Info,
      }
    case 'LOW':
      return {
        color: 'text-blue-400',
        bg: 'bg-blue-500/10',
        border: 'border-blue-500/30',
        label: 'Low',
        icon: CheckCircle2,
      }
  }
}

const renderSummaryBadges = (recommendation: Recommendation) => {
  const items: string[] = []

  if (recommendation.evidenceCount !== undefined) {
    items.push(`Evidence ${recommendation.evidenceCount}`)
  }
  if (recommendation.affectedFilesCount !== undefined) {
    items.push(`Files ${recommendation.affectedFilesCount}`)
  }
  if ((recommendation.scannerTypes?.length ?? 0) > 0) {
    items.push(recommendation.scannerTypes!.join(', '))
  }

  if (items.length === 0) {
    return <span className="text-xs text-slate-500">Planner summary not available</span>
  }

  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <span
          key={`${recommendation.id}-${item}`}
          className="inline-flex rounded-md bg-white/5 px-2 py-1 text-xs text-slate-300"
        >
          {item}
        </span>
      ))}
    </div>
  )
}

export const RecommendationTable = ({
  recommendations,
  onRecommendationClick,
}: RecommendationTableProps) => {
  if (recommendations.length === 0) {
    return (
      <div className="rounded-xl border border-white/10 bg-white/5 p-12 text-center backdrop-blur-md">
        <Sparkles className="mx-auto mb-4 h-12 w-12 text-slate-400" />
        <p className="mb-2 text-lg font-medium text-slate-300">No recommendations found</p>
        <p className="text-sm text-slate-500">
          Try adjusting your filters to see more recommendations.
        </p>
      </div>
    )
  }

  return (
    <div className="overflow-hidden rounded-xl border border-white/10 bg-white/5 backdrop-blur-md">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/10">
              <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">
                Priority
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">
                Migration Target
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">
                Algorithms
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">
                Evidence
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">
                Priority Reason
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">
                Effort
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {recommendations.map((recommendation) => {
              const priorityConfig = getPriorityConfig(recommendation.priority)
              const PriorityIcon = priorityConfig.icon

              return (
                <tr
                  key={recommendation.id}
                  onClick={() => onRecommendationClick(recommendation)}
                  className="group cursor-pointer transition-colors duration-200 hover:bg-white/5"
                >
                  <td className="whitespace-nowrap px-6 py-4 align-top">
                    <div
                      className={`inline-flex items-center gap-2 rounded-lg border px-3 py-1.5 ${priorityConfig.bg} ${priorityConfig.border}`}
                    >
                      <PriorityIcon className={`h-4 w-4 ${priorityConfig.color}`} />
                      <span className={`text-sm font-semibold ${priorityConfig.color}`}>
                        {priorityConfig.label}
                      </span>
                    </div>
                    <p className="mt-2 text-xs text-slate-500">Rank #{recommendation.priorityRank}</p>
                  </td>
                  <td className="px-6 py-4 align-top">
                    <div className="flex items-center gap-2">
                      <div className="rounded border border-indigo-500/20 bg-indigo-500/10 p-1.5">
                        <FileCode className="h-4 w-4 text-indigo-400" />
                      </div>
                      <span className="font-medium text-white transition-colors group-hover:text-indigo-400">
                        {recommendation.issueName}
                      </span>
                    </div>
                    {recommendation.normalizedClass && (
                      <span className="mt-2 inline-flex rounded-full border border-indigo-400/20 bg-indigo-500/10 px-2.5 py-1 text-[11px] uppercase tracking-[0.12em] text-indigo-300">
                        {recommendation.normalizedClass}
                      </span>
                    )}
                    {recommendation.filePath && (
                      <code className="mt-2 block font-mono text-xs text-slate-400">
                        {recommendation.filePath}
                      </code>
                    )}
                    {recommendation.nistStandardReference && (
                      <p className="mt-1 text-xs text-indigo-300">
                        {getDisplayValue(recommendation.nistStandardReference)}
                      </p>
                    )}
                  </td>
                  <td className="px-6 py-4 align-top">
                    <div className="space-y-2">
                      <div>
                        <p className="text-[11px] uppercase tracking-[0.12em] text-slate-500">Current</p>
                        <span className="font-mono text-sm text-red-300">{recommendation.targetAlgorithm}</span>
                      </div>
                      <div>
                        <p className="text-[11px] uppercase tracking-[0.12em] text-slate-500">Recommended</p>
                        <span
                          className="font-mono text-sm text-green-300"
                          title={
                            hasDisplayValue(recommendation.recommendedPQCAlgorithm)
                              ? undefined
                              : 'A specific PQC replacement was not returned by the analysis.'
                          }
                        >
                          {getDisplayValue(recommendation.recommendedPQCAlgorithm, 'Not specified')}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 align-top">{renderSummaryBadges(recommendation)}</td>
                  <td className="px-6 py-4 align-top">
                    <p className="max-w-[24rem] text-sm leading-relaxed text-slate-300">
                      {getDisplayValue(
                        recommendation.priorityReason || recommendation.analysisSummary || recommendation.context,
                        'Priority rationale not available',
                      )}
                    </p>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 align-top">
                    <span className="text-sm text-slate-300">{recommendation.estimatedEffort}</span>
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
