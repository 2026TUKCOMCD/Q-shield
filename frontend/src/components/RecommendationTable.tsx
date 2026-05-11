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
  fallback = '정보 없음',
) => (hasDisplayValue(value) ? value.trim() : fallback)

const getPriorityConfig = (priority: Priority) => {
  switch (priority) {
    case 'CRITICAL':
      return {
        color: 'text-red-400',
        bg: 'bg-red-500/10',
        border: 'border-red-500/30',
        label: '긴급',
        icon: AlertCircle,
      }
    case 'HIGH':
      return {
        color: 'text-orange-400',
        bg: 'bg-orange-500/10',
        border: 'border-orange-500/30',
        label: '높음',
        icon: AlertTriangle,
      }
    case 'MEDIUM':
      return {
        color: 'text-yellow-400',
        bg: 'bg-yellow-500/10',
        border: 'border-yellow-500/30',
        label: '보통',
        icon: Info,
      }
    case 'LOW':
      return {
        color: 'text-blue-400',
        bg: 'bg-blue-500/10',
        border: 'border-blue-500/30',
        label: '낮음',
        icon: CheckCircle2,
      }
  }
}


const getPrioritySignalTags = (recommendation: Recommendation) => {
  const tags: { label: string; className: string }[] = []

  const priority = recommendation.priority
  const severityClass =
    priority === 'CRITICAL'
      ? 'border-red-500/30 bg-red-500/10 text-red-300'
      : priority === 'HIGH'
        ? 'border-orange-500/30 bg-orange-500/10 text-orange-300'
        : priority === 'MEDIUM'
          ? 'border-yellow-500/30 bg-yellow-500/10 text-yellow-300'
          : 'border-blue-500/30 bg-blue-500/10 text-blue-300'
  tags.push({ label: priority, className: severityClass })

  const hits = recommendation.evidenceCount
  if (hits !== undefined) {
    tags.push({ label: `${hits}건`, className: 'border-white/10 bg-white/5 text-slate-300' })
  }

  const files = recommendation.affectedFilesCount ?? recommendation.evidence?.affectedFilesCount
  if (files !== undefined) {
    tags.push({ label: `${files}개 파일`, className: 'border-white/10 bg-white/5 text-slate-300' })
  }

  const scanners = recommendation.scannerTypes ?? recommendation.evidence?.scannerTypes ?? []
  scanners.forEach((s) => {
    tags.push({
      label: s.toUpperCase(),
      className: 'border-indigo-400/20 bg-indigo-500/10 text-indigo-300',
    })
  })

  return tags
}

const getAnalysisModeBadge = (mode?: Recommendation['analysisMode']) => {
  switch (mode) {
    case 'real':
      return {
        label: 'AI 분석',
        className: 'border-emerald-400/20 bg-emerald-500/10 text-emerald-300',
      }
    case 'fallback':
      return {
        label: 'AI 대체',
        className: 'border-amber-400/20 bg-amber-500/10 text-amber-300',
      }
    case 'mock':
      return {
        label: 'AI 모의',
        className: 'border-sky-400/20 bg-sky-500/10 text-sky-300',
      }
    case 'error':
      return {
        label: 'AI 오류',
        className: 'border-rose-400/20 bg-rose-500/10 text-rose-300',
      }
    default:
      return {
        label: '규칙 기반',
        className: 'border-white/10 bg-white/5 text-slate-300',
      }
  }
}

export const RecommendationTable = ({
  recommendations,
  onRecommendationClick,
}: RecommendationTableProps) => {
  if (recommendations.length === 0) {
    return (
      <div className="rounded-xl border border-white/10 bg-white/5 p-12 text-center backdrop-blur-md">
        <Sparkles className="mx-auto mb-4 h-12 w-12 text-slate-400" />
        <p className="mb-2 text-lg font-medium text-slate-300">추천 항목이 없습니다</p>
        <p className="text-sm text-slate-500">
          필터를 조정해 더 많은 추천을 확인해 보세요.
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
                우선순위
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">
                마이그레이션 대상
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">
                현재 → 권장 알고리즘
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">
                위험 신호
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">
                예상 공수
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {recommendations.map((recommendation) => {
              const priorityConfig = getPriorityConfig(recommendation.priority)
              const PriorityIcon = priorityConfig.icon
              const analysisModeBadge = getAnalysisModeBadge(recommendation.analysisMode)

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
                    <p className="mt-2 text-xs text-slate-500">순위 #{recommendation.priorityRank}</p>
                    <span
                      className={`mt-2 inline-flex rounded-full border px-2.5 py-1 text-[11px] ${analysisModeBadge.className}`}
                    >
                      {analysisModeBadge.label}
                    </span>
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
                        <p className="text-[11px] uppercase tracking-[0.12em] text-slate-500">현재</p>
                        <span className="font-mono text-sm text-red-300">{recommendation.targetAlgorithm}</span>
                      </div>
                      <div>
                        <p className="text-[11px] uppercase tracking-[0.12em] text-slate-500">권장</p>
                        <span
                          className="font-mono text-sm text-green-300"
                          title={
                            hasDisplayValue(recommendation.recommendedPQCAlgorithm)
                              ? undefined
                              : '분석에서 PQC 대체 알고리즘이 반환되지 않았습니다.'
                          }
                        >
                          {getDisplayValue(recommendation.recommendedPQCAlgorithm, '미지정')}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 align-top">
                    <div className="flex flex-wrap gap-1.5">
                      {getPrioritySignalTags(recommendation).map((tag) => (
                        <span
                          key={`${recommendation.id}-tag-${tag.label}`}
                          className={`inline-flex rounded-full border px-2.5 py-1 text-[11px] font-medium ${tag.className}`}
                        >
                          {tag.label}
                        </span>
                      ))}
                    </div>
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
