import { type Priority } from '../services/recommendationService'
import { Filter, X } from 'lucide-react'

interface RecommendationFiltersProps {
  algorithmType: string
  context: string
  priority: Priority | ''
  onAlgorithmTypeChange: (value: string) => void
  onContextChange: (value: string) => void
  onPriorityChange: (value: Priority | '') => void
  onReset: () => void
}

/**
 * Recommendation Filters 컴포넌트
 * T017: 알고리즘 타입 및 컨텍스트 필터링 UI
 */
export const RecommendationFilters = ({
  algorithmType,
  context,
  priority,
  onAlgorithmTypeChange,
  onContextChange,
  onPriorityChange,
  onReset,
}: RecommendationFiltersProps) => {
  const hasActiveFilters = algorithmType !== '' || context !== '' || priority !== ''

  return (
    <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-gradient-to-br from-indigo-500/20 to-purple-600/20 rounded-lg border border-indigo-500/30">
          <Filter className="w-5 h-5 text-indigo-400" />
        </div>
        <h2 className="text-xl font-semibold text-white">Filters</h2>
        {hasActiveFilters && (
          <button
            onClick={onReset}
            className="ml-auto px-3 py-1.5 text-xs text-slate-400 hover:text-white bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg transition-colors flex items-center gap-2"
          >
            <X className="w-3 h-3" />
            Reset
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Algorithm Type Filter */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Algorithm Type</label>
          <input
            type="text"
            value={algorithmType}
            onChange={(e) => onAlgorithmTypeChange(e.target.value)}
            placeholder="e.g., RSA, SHA, AES"
            className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all"
          />
        </div>

        {/* Context Filter */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Context</label>
          <input
            type="text"
            value={context}
            onChange={(e) => onContextChange(e.target.value)}
            placeholder="e.g., authentication, payment"
            className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all"
          />
        </div>

        {/* Priority Filter */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Priority</label>
          <select
            value={priority}
            onChange={(e) => onPriorityChange(e.target.value as Priority | '')}
            className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all"
          >
            <option value="">All Priorities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>
      </div>
    </div>
  )
}
