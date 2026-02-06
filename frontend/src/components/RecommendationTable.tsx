import { type Recommendation, type Priority } from '../services/recommendationService'
import { FileCode, AlertCircle, AlertTriangle, Info, CheckCircle2, Sparkles } from 'lucide-react'

interface RecommendationTableProps {
  recommendations: Recommendation[]
  onRecommendationClick: (recommendation: Recommendation) => void
}

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

export const RecommendationTable = ({
  recommendations,
  onRecommendationClick,
}: RecommendationTableProps) => {
  if (recommendations.length === 0) {
    return (
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-12 text-center">
        <Sparkles className="w-12 h-12 mx-auto mb-4 text-slate-400" />
        <p className="text-slate-300 text-lg mb-2 font-medium">No recommendations found</p>
        <p className="text-slate-500 text-sm">
          Try adjusting your filters to see more recommendations.
        </p>
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
                Priority
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Issue
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Target Algorithm
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Recommended PQC
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Context
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
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
                  className="hover:bg-white/5 transition-colors duration-200 cursor-pointer group"
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div
                      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg ${priorityConfig.bg} ${priorityConfig.border} border`}
                    >
                      <PriorityIcon className={`w-4 h-4 ${priorityConfig.color}`} />
                      <span className={`text-sm font-semibold ${priorityConfig.color}`}>
                        {priorityConfig.label}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 bg-indigo-500/10 rounded border border-indigo-500/20">
                        <FileCode className="w-4 h-4 text-indigo-400" />
                      </div>
                      <span className="text-white font-medium group-hover:text-indigo-400 transition-colors">
                        {recommendation.issueName}
                      </span>
                    </div>
                    {recommendation.filePath && (
                      <code className="text-xs text-slate-400 font-mono mt-1 block">
                        {recommendation.filePath}
                      </code>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-red-300 font-mono text-sm">{recommendation.targetAlgorithm}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-green-300 font-mono text-sm">
                      {recommendation.recommendedPQCAlgorithm}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-1 text-xs bg-white/5 text-slate-300 rounded">
                      {recommendation.context}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-slate-300 text-sm">{recommendation.estimatedEffort}</span>
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


