import { useEffect, useMemo, useRef, useState } from 'react'
import { ChevronDown, Filter, X } from 'lucide-react'

import { type Priority } from '../services/aiRecommendationService'

interface RecommendationFiltersProps {
  algorithmType: string
  priority: Priority | ''
  onAlgorithmTypeChange: (value: string) => void
  onPriorityChange: (value: Priority | '') => void
  onReset: () => void
}

const priorityOptions: Array<{ label: string; value: Priority | '' }> = [
  { label: 'All Priorities', value: '' },
  { label: 'Critical', value: 'CRITICAL' },
  { label: 'High', value: 'HIGH' },
  { label: 'Medium', value: 'MEDIUM' },
  { label: 'Low', value: 'LOW' },
]

export const RecommendationFilters = ({
  algorithmType,
  priority,
  onAlgorithmTypeChange,
  onPriorityChange,
  onReset,
}: RecommendationFiltersProps) => {
  const [isPriorityMenuOpen, setIsPriorityMenuOpen] = useState(false)
  const priorityMenuRef = useRef<HTMLDivElement | null>(null)
  const hasActiveFilters = algorithmType !== '' || priority !== ''
  const selectedPriorityLabel = useMemo(
    () => priorityOptions.find((option) => option.value === priority)?.label ?? 'All Priorities',
    [priority],
  )

  useEffect(() => {
    if (!isPriorityMenuOpen) {
      return
    }

    const handleClickOutside = (event: MouseEvent) => {
      if (!priorityMenuRef.current?.contains(event.target as Node)) {
        setIsPriorityMenuOpen(false)
      }
    }

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsPriorityMenuOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleEscape)

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [isPriorityMenuOpen])

  return (
    <div className="relative z-20 overflow-visible bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-6">
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

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Algorithm Type</label>
          <input
            type="text"
            value={algorithmType}
            onChange={(event) => onAlgorithmTypeChange(event.target.value)}
            placeholder="e.g., RSA, SHA, AES"
            className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all"
          />
        </div>
        <div ref={priorityMenuRef} className="relative z-30">
          <label className="block text-sm font-medium text-slate-300 mb-2">Priority</label>
          <button
            type="button"
            onClick={() => setIsPriorityMenuOpen((current) => !current)}
            className={`w-full px-4 py-2.5 bg-white/5 border rounded-lg text-white transition-all flex items-center justify-between ${
              isPriorityMenuOpen
                ? 'border-indigo-500/60 ring-2 ring-indigo-500/30'
                : 'border-white/10 hover:border-indigo-500/40'
            }`}
            aria-haspopup="listbox"
            aria-expanded={isPriorityMenuOpen}
          >
            <span>{selectedPriorityLabel}</span>
            <ChevronDown
              className={`w-4 h-4 text-slate-300 transition-transform ${
                isPriorityMenuOpen ? 'rotate-180' : ''
              }`}
            />
          </button>

          {isPriorityMenuOpen && (
            <div className="absolute left-0 right-0 z-50 mt-2 overflow-hidden rounded-lg border border-indigo-400/30 bg-[#1b173a] shadow-2xl shadow-black/50">
              <div className="py-1" role="listbox" aria-label="Priority">
                {priorityOptions.map((option) => {
                  const isSelected = option.value === priority

                  return (
                    <button
                      key={option.label}
                      type="button"
                      onClick={() => {
                        onPriorityChange(option.value)
                        setIsPriorityMenuOpen(false)
                      }}
                      className={`flex w-full items-center px-4 py-2.5 text-left text-sm transition-colors ${
                        isSelected
                          ? 'bg-indigo-500/25 text-indigo-100'
                          : 'text-slate-100 hover:bg-indigo-500/15 hover:text-white'
                      }`}
                      role="option"
                      aria-selected={isSelected}
                    >
                      {option.label}
                    </button>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
