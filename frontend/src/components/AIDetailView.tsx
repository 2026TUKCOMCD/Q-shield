import { type ReactNode, useEffect, useState } from 'react'
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Code,
  Database,
  FileCode,
  FolderTree,
  Info,
  Loader2,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  X,
} from 'lucide-react'

import { type Priority, type Recommendation } from '../services/aiRecommendationService'

interface AIDetailViewProps {
  recommendation: Recommendation | null
  isOpen: boolean
  onClose: () => void
  onRetryCitations?: () => Promise<void>
}

const getPriorityIcon = (priority: Priority) => {
  switch (priority) {
    case 'CRITICAL':
      return AlertCircle
    case 'HIGH':
      return AlertTriangle
    case 'MEDIUM':
      return Info
    case 'LOW':
      return CheckCircle2
  }
}

const hasMeaningfulValue = (value?: string | null): value is string => {
  if (!value) {
    return false
  }

  const normalizedValue = value.trim()
  return normalizedValue !== '' && normalizedValue.toUpperCase() !== 'N/A'
}

const getDisplayValue = (value?: string | null, fallback = 'Not available') =>
  hasMeaningfulValue(value) ? value.trim() : fallback

const renderMarkdown = (text: string) => {
  const lines = text.split('\n')
  const elements: ReactNode[] = []
  let currentCodeBlock: string[] = []
  let inCodeBlock = false

  lines.forEach((line, index) => {
    if (line.startsWith('```')) {
      if (inCodeBlock) {
        elements.push(
          <pre
            key={`code-${index}`}
            className="my-4 overflow-x-auto rounded-lg border border-white/10 bg-slate-900/50 p-4"
          >
            <code className="font-mono text-sm text-slate-200">{currentCodeBlock.join('\n')}</code>
          </pre>,
        )
        currentCodeBlock = []
        inCodeBlock = false
      } else {
        inCodeBlock = true
      }
      return
    }

    if (inCodeBlock) {
      currentCodeBlock.push(line)
      return
    }

    if (line.startsWith('## ')) {
      elements.push(
        <h2 key={index} className="mt-6 mb-3 text-xl font-bold text-white">
          {line.replace('## ', '')}
        </h2>,
      )
      return
    }

    if (line.startsWith('### ')) {
      elements.push(
        <h3 key={index} className="mt-4 mb-2 text-lg font-semibold text-slate-200">
          {line.replace('### ', '')}
        </h3>,
      )
      return
    }

    if (line.startsWith('- ')) {
      elements.push(
        <li key={index} className="mb-1 ml-4 text-slate-300">
          {line.replace('- ', '')}
        </li>,
      )
      return
    }

    if (line.trim() !== '') {
      elements.push(
        <p key={index} className="mb-3 leading-relaxed text-slate-300">
          {line}
        </p>,
      )
    } else {
      elements.push(<br key={index} />)
    }
  })

  if (inCodeBlock && currentCodeBlock.length > 0) {
    elements.push(
      <pre
        key="code-final"
        className="my-4 overflow-x-auto rounded-lg border border-white/10 bg-slate-900/50 p-4"
      >
        <code className="font-mono text-sm text-slate-200">{currentCodeBlock.join('\n')}</code>
      </pre>,
    )
  }

  return elements
}

const extractPrimaryGuide = (text: string) => {
  const stopHeaders = new Set([
    '### nist standard reference',
    '### confidence',
    '### analysis summary',
    '### supporting citations',
  ])
  const lines = text.split('\n')

  while (lines[0]?.trim() === '') {
    lines.shift()
  }

  if (lines[0]?.startsWith('## ')) {
    lines.shift()
  }

  const primaryLines: string[] = []

  for (const line of lines) {
    const normalizedLine = line.trim().toLowerCase()
    if (stopHeaders.has(normalizedLine)) {
      break
    }
    primaryLines.push(line)
  }

  return primaryLines.join('\n').trim()
}

const getEvidenceCounts = (recommendation: Recommendation) => {
  const plannerScannerTypes = recommendation.evidence?.scannerTypes ?? []
  const plannerEvidenceCount = recommendation.evidence?.evidenceCount

  if (plannerScannerTypes.length > 0 && plannerEvidenceCount !== undefined) {
    const distributed = Math.max(1, Math.ceil(plannerEvidenceCount / Math.max(1, plannerScannerTypes.length)))
    return plannerScannerTypes.map((scannerType) => `${scannerType.toUpperCase()}=${distributed}`)
  }

  const countsByScannerType = recommendation.inputsSummary?.counts_by_scanner_type

  if (countsByScannerType && typeof countsByScannerType === 'object' && !Array.isArray(countsByScannerType)) {
    const entries = Object.entries(countsByScannerType as Record<string, unknown>)
      .map(([label, rawValue]) => {
        const value = typeof rawValue === 'number' ? rawValue : Number(rawValue)
        if (!Number.isFinite(value)) {
          return null
        }

        return `${label.toUpperCase()}=${Math.round(value)}`
      })
      .filter((entry): entry is string => entry !== null)

    if (entries.length > 0) {
      return entries
    }
  }

  if ((recommendation.scannerTypes?.length ?? 0) > 0 && recommendation.evidenceCount !== undefined) {
    const distributed = Math.max(
      1,
      Math.ceil(recommendation.evidenceCount / Math.max(1, recommendation.scannerTypes!.length)),
    )
    return recommendation.scannerTypes!.map((scannerType) => `${scannerType.toUpperCase()}=${distributed}`)
  }

  const summarySource = `${recommendation.analysisSummary ?? ''} ${recommendation.context ?? ''}`
  const matches = Array.from(
    summarySource.matchAll(/\b([A-Z][A-Z0-9_-]*)\s*=\s*(\d+)\b/g),
    (match) => `${match[1]}=${match[2]}`,
  )

  return Array.from(new Set(matches))
}

const getEvidenceTotal = (evidenceCounts: string[]) =>
  evidenceCounts.reduce((total, entry) => {
    const value = Number(entry.split('=')[1] ?? 0)
    return Number.isFinite(value) ? total + value : total
  }, 0)

const getConfidenceFillClass = (confidencePercent: number | null) => {
  if (confidencePercent === null) {
    return 'bg-slate-600'
  }

  if (confidencePercent >= 75) {
    return 'bg-gradient-to-r from-emerald-400 to-teal-400'
  }

  if (confidencePercent >= 50) {
    return 'bg-gradient-to-r from-indigo-400 to-purple-500'
  }

  if (confidencePercent >= 30) {
    return 'bg-gradient-to-r from-amber-400 to-orange-500'
  }

  return 'bg-gradient-to-r from-red-400 to-pink-500'
}

const SummaryCard = ({
  label,
  value,
  className = 'text-slate-200',
}: {
  label: string
  value: string
  className?: string
}) => (
  <div className="rounded-xl border border-white/10 bg-white/5 p-4">
    <p className="mb-2 text-[11px] uppercase tracking-[0.2em] text-slate-500">{label}</p>
    <p className={`text-sm font-semibold ${className}`}>{value}</p>
  </div>
)

const getSourceBadgeConfig = (sourceType?: string | null) => {
  switch ((sourceType || '').toUpperCase()) {
    case 'NIST_STANDARD':
      return {
        label: 'NIST Standard',
        className: 'border-emerald-400/20 bg-emerald-500/10 text-emerald-300',
      }
    case 'NIST_GUIDE':
      return {
        label: 'NIST Guide',
        className: 'border-indigo-400/20 bg-indigo-500/10 text-indigo-300',
      }
    case 'BENCHMARK':
      return {
        label: 'Benchmark',
        className: 'border-amber-400/20 bg-amber-500/10 text-amber-300',
      }
    case 'ACADEMIC_PAPER':
      return {
        label: 'Paper',
        className: 'border-fuchsia-400/20 bg-fuchsia-500/10 text-fuchsia-300',
      }
    default:
      return {
        label: sourceType || 'Source',
        className: 'border-white/10 bg-white/5 text-slate-300',
      }
  }
}

const normalizeCitationGroup = (sourceType?: string | null) => {
  const normalized = (sourceType || '').toUpperCase()
  if (normalized === 'NIST_STANDARD' || normalized === 'NIST_GUIDE') {
    return 'normative'
  }
  if (normalized === 'BENCHMARK' || normalized === 'ACADEMIC_PAPER') {
    return 'benchmark'
  }
  return 'other'
}

const getAnalysisModeConfig = (mode?: 'real' | 'fallback' | 'mock' | 'error') => {
  switch (mode) {
    case 'real':
      return { label: 'Real Analysis', className: 'border-emerald-400/20 bg-emerald-500/10 text-emerald-300' }
    case 'fallback':
      return { label: 'Fallback Analysis', className: 'border-amber-400/20 bg-amber-500/10 text-amber-300' }
    case 'mock':
      return { label: 'Mock Analysis', className: 'border-sky-400/20 bg-sky-500/10 text-sky-300' }
    case 'error':
      return { label: 'Error State', className: 'border-rose-400/20 bg-rose-500/10 text-rose-300' }
    default:
      return null
  }
}

export const AIDetailView = ({
  recommendation,
  isOpen,
  onClose,
  onRetryCitations,
}: AIDetailViewProps) => {
  const [isRetrying, setIsRetrying] = useState(false)
  const [retryMessage, setRetryMessage] = useState<string | null>(null)

  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        onClose()
      }
    }

    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  useEffect(() => {
    setIsRetrying(false)
    setRetryMessage(null)
  }, [isOpen, recommendation?.id])

  if (!isOpen || !recommendation) {
    return null
  }

  const PriorityIcon = getPriorityIcon(recommendation.priority)
  const hasNistReference = hasMeaningfulValue(recommendation.nistStandardReference)
  const hasCitations = (recommendation.citations?.length ?? 0) > 0
  const hasNistEvidence = hasNistReference || hasCitations
  const plannerEvidence = recommendation.evidence
  const structuredGuidance = recommendation.guidance
  const structuredTrust = recommendation.trust
  const confidencePercent =
    (recommendation.confidence ?? structuredTrust?.confidence) === undefined
      ? null
      : Math.round(
          Math.max(0, Math.min(1, recommendation.confidence ?? structuredTrust?.confidence ?? 0)) * 100,
        )
  const primaryGuide = extractPrimaryGuide(recommendation.aiRecommendation || structuredGuidance?.summary || '')
  const evidenceCounts = getEvidenceCounts(recommendation)
  const evidenceTotal =
    recommendation.evidenceCount !== undefined
      ? recommendation.evidenceCount
      : plannerEvidence?.evidenceCount !== undefined
        ? plannerEvidence.evidenceCount
        : getEvidenceTotal(evidenceCounts)
  const findingsSummary = getDisplayValue(recommendation.analysisSummary || recommendation.context)
  const duplicateSignal = `${recommendation.analysisSummary ?? ''} ${recommendation.context ?? ''}`.toLowerCase()
  const duplicateState =
    duplicateSignal.includes('dedup') || duplicateSignal.includes('duplicate') ? 'confirmed' : 'unknown'
  const affectedLocations = recommendation.affectedLocations ?? []
  const affectedFilePaths = recommendation.affectedFilePaths ?? plannerEvidence?.affectedFilePaths ?? []
  const codeFixExamples = recommendation.codeFixExamples ?? []
  const scannerTypes = recommendation.scannerTypes ?? plannerEvidence?.scannerTypes ?? []
  const validationChecklist =
    recommendation.validationChecklist ?? structuredGuidance?.validationChecklist ?? []
  const benchmarkNotes = recommendation.benchmarkNotes ?? structuredGuidance?.benchmarkNotes ?? []
  const benchmarkSupport = structuredGuidance?.benchmarkSupport ?? []
  const assumptions = recommendation.assumptions ?? structuredGuidance?.assumptions ?? []
  const priorityReason =
    recommendation.priorityReason ?? plannerEvidence?.priorityReason ?? 'Deterministic priority rationale not available'
  const confidenceReason = recommendation.confidenceReason ?? structuredTrust?.confidenceReason
  const analysisMode = recommendation.analysisMode ?? structuredTrust?.analysisMode
  const citationsAvailable = recommendation.citationsAvailable ?? structuredTrust?.citationsAvailable ?? hasCitations
  const ragCorpusLoaded = recommendation.ragCorpusLoaded ?? structuredTrust?.ragCorpusLoaded ?? false
  const normativeEvidenceCount =
    plannerEvidence?.normativeEvidenceCount ?? structuredTrust?.normativeEvidenceCount ?? 0
  const analysisModeConfig = getAnalysisModeConfig(analysisMode)
  const priorityFactors = (plannerEvidence?.priorityFactors ?? [])
    .filter((factor) => factor.score > 0)
    .sort((left, right) => right.score - left.score)
  const affectedFilesCount =
    recommendation.affectedFilesCount ?? plannerEvidence?.affectedFilesCount ?? affectedFilePaths.length
  const relatedAssetRefs = plannerEvidence?.relatedAssetRefs ?? []
  const correlationRefs = plannerEvidence?.correlationRefs ?? []
  const citationEvidenceRows = (recommendation.citations ?? []).map((citation) => {
    const sectionText = hasMeaningfulValue(citation.section)
      ? citation.section.trim()
      : citation.page
        ? `page ${citation.page}`
        : 'Section not available'
    const pageText = citation.page ? `, p.${citation.page}` : ''
    return {
      key: `${citation.doc_id}:${citation.page ?? 'na'}:${sectionText}`,
      title: getDisplayValue(citation.title, 'NIST citation'),
      location: `${sectionText}${pageText}`,
      sourceType: citation.source_type ?? 'UNKNOWN',
      claimType: citation.claim_type ?? 'unknown',
      topic: citation.topic ?? 'general',
      authorityWeight: citation.authority_weight ?? null,
    }
  })
  const normativeCitationRows = citationEvidenceRows.filter((row) => normalizeCitationGroup(row.sourceType) === 'normative')
  const benchmarkCitationRows = citationEvidenceRows.filter((row) => normalizeCitationGroup(row.sourceType) === 'benchmark')
  const otherCitationRows = citationEvidenceRows.filter((row) => normalizeCitationGroup(row.sourceType) === 'other')
  const canRetryCitations = typeof onRetryCitations === 'function'

  const handleRetryCitations = async () => {
    if (!onRetryCitations) {
      return
    }

    setIsRetrying(true)
    setRetryMessage(null)

    try {
      await onRetryCitations()
      setRetryMessage('Citation refresh requested. This panel updates when new evidence is returned.')
    } catch {
      setRetryMessage('Citation refresh could not be completed right now.')
    } finally {
      setIsRetrying(false)
    }
  }

  const renderCitationGroup = (
    title: string,
    description: string,
    rows: typeof citationEvidenceRows,
  ) => {
    if (rows.length === 0) {
      return null
    }

    return (
      <div className="space-y-3 rounded-xl border border-white/10 bg-white/5 p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-white">{title}</p>
            <p className="mt-1 text-xs text-slate-400">{description}</p>
          </div>
          <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-slate-300">
            {rows.length}
          </span>
        </div>
        <div className="space-y-3">
          {rows.map((row) => {
            const badge = getSourceBadgeConfig(row.sourceType)
            return (
              <div key={row.key} className="rounded-lg border border-white/10 bg-white/5 p-3">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-white">{row.title}</p>
                    <p className="mt-1 text-xs text-indigo-300">{row.location}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <span className={`rounded-full border px-2.5 py-1 text-[11px] ${badge.className}`}>
                      {badge.label}
                    </span>
                    <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[11px] text-slate-300">
                      {row.claimType}
                    </span>
                  </div>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  <span className="rounded-md border border-white/10 bg-slate-900/40 px-2 py-1 text-xs text-slate-300">
                    topic: {row.topic}
                  </span>
                  {row.authorityWeight !== null && (
                    <span className="rounded-md border border-white/10 bg-slate-900/40 px-2 py-1 text-xs text-slate-300">
                      authority: {row.authorityWeight}
                    </span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  return (
    <>
      <div
        className="fixed inset-0 z-50 animate-in bg-black/60 backdrop-blur-sm fade-in duration-200"
        onClick={onClose}
      />
      <div className="pointer-events-none fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          className="pointer-events-auto flex max-h-[90vh] w-full max-w-4xl animate-in flex-col overflow-hidden rounded-2xl border border-white/10 bg-[#020617] shadow-2xl fade-in slide-in-from-bottom-4 duration-300"
          onClick={(event) => event.stopPropagation()}
        >
          <div className="border-b border-white/10 bg-gradient-to-r from-indigo-500/10 to-purple-600/10 p-6">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="mb-2 flex items-center gap-3">
                  <div className="rounded-lg border border-indigo-500/30 bg-gradient-to-br from-indigo-500/20 to-purple-600/20 p-2">
                    <Sparkles className="h-5 w-5 text-indigo-400" />
                  </div>
                  <div className="flex items-center gap-2">
                    <PriorityIcon className="h-5 w-5 text-indigo-400" />
                    <span className="rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-sm font-medium text-indigo-400">
                      {recommendation.priority}
                    </span>
                    {analysisModeConfig && (
                      <span className={`rounded-full border px-3 py-1 text-xs ${analysisModeConfig.className}`}>
                        {analysisModeConfig.label}
                      </span>
                    )}
                    {recommendation.normalizedClass && (
                      <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs uppercase tracking-[0.14em] text-slate-300">
                        {recommendation.normalizedClass}
                      </span>
                    )}
                  </div>
                </div>
                <h2 className="mb-2 text-2xl font-bold text-white">{recommendation.issueName}</h2>
                <div className="flex flex-wrap items-center gap-4 text-sm text-slate-400">
                  <div className="flex items-center gap-2">
                    <Code className="h-4 w-4" />
                    <span>
                      <span className="text-red-300">{recommendation.targetAlgorithm}</span>
                      {' -> '}
                      <span className="text-green-300">
                        {getDisplayValue(recommendation.recommendedPQCAlgorithm, 'Not specified')}
                      </span>
                    </span>
                  </div>
                  {recommendation.filePath && (
                    <code className="rounded bg-white/5 px-2 py-1 font-mono text-xs">
                      {recommendation.filePath}
                    </code>
                  )}
                  <span>Effort: {getDisplayValue(recommendation.estimatedEffort, 'Not available')}</span>
                </div>
              </div>
              <button
                onClick={onClose}
                className="flex-shrink-0 rounded-lg p-2 text-slate-400 transition-colors hover:bg-white/10 hover:text-white"
                aria-label="Close"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-6">
            <div className="space-y-6">
              <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
                <SummaryCard label="Target Algorithm" value={recommendation.targetAlgorithm} className="text-red-300" />
                <SummaryCard
                  label="Recommended PQC"
                  value={getDisplayValue(recommendation.recommendedPQCAlgorithm, 'Not specified')}
                  className="text-green-300"
                />
                <SummaryCard
                  label="Evidence Count"
                  value={String(evidenceTotal || 0)}
                />
                <SummaryCard label="Affected Files" value={String(affectedFilesCount || 0)} />
                <SummaryCard
                  label="Scanner Sources"
                  value={scannerTypes.length > 0 ? scannerTypes.join(', ') : 'Not available'}
                />
                <SummaryCard
                  label="Confidence"
                  value={confidencePercent === null ? 'Not available' : `${confidencePercent}%`}
                  className="text-slate-100"
                />
              </div>

              <div className="rounded-r-lg border-l-4 border-indigo-500/50 bg-gradient-to-r from-indigo-500/5 to-purple-600/5 p-4">
                <p className="text-sm leading-relaxed text-slate-200">
                  <strong className="text-white">Migration planning mode</strong>
                  <br />
                  This recommendation combines deterministic planner evidence with AI-generated guidance.
                  Use the priority rationale and affected assets first, then validate example code and citations.
                </p>
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
                <div className="mb-4 flex items-center gap-2">
                  <ShieldCheck className="h-5 w-5 text-indigo-300" />
                  <h3 className="text-lg font-semibold text-white">Priority Basis</h3>
                </div>
                <div className="space-y-4">
                  <div>
                    <p className="mb-2 text-xs uppercase tracking-[0.15em] text-slate-500">Priority Reason</p>
                    <p className="text-sm leading-relaxed text-slate-300">{priorityReason}</p>
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <div className="mb-2 flex items-center gap-2">
                        <Database className="h-4 w-4 text-indigo-300" />
                        <p className="text-xs uppercase tracking-[0.15em] text-slate-500">Evidence Signals</p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {evidenceCounts.length > 0 ? (
                          evidenceCounts.map((entry) => (
                            <span
                              key={`${recommendation.id}-${entry}`}
                              className="rounded-md border border-white/10 bg-white/5 px-2 py-1 text-xs text-slate-300"
                            >
                              {entry}
                            </span>
                          ))
                        ) : (
                          <span className="text-sm text-slate-500">Signal counts not available</span>
                        )}
                      </div>
                    </div>
                    <div>
                      <div className="mb-2 flex items-center gap-2">
                        <FolderTree className="h-4 w-4 text-indigo-300" />
                        <p className="text-xs uppercase tracking-[0.15em] text-slate-500">Affected Asset Scope</p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {affectedFilePaths.length > 0 ? (
                          affectedFilePaths.slice(0, 8).map((path) => (
                            <code
                              key={`${recommendation.id}-${path}`}
                              className="rounded-md border border-white/10 bg-white/5 px-2 py-1 text-xs text-slate-300"
                            >
                              {path}
                            </code>
                          ))
                        ) : (
                          <span className="text-sm text-slate-500">Affected files were not returned</span>
                        )}
                      </div>
                      {(relatedAssetRefs.length > 0 || correlationRefs.length > 0) && (
                        <div className="mt-3 space-y-3">
                          {relatedAssetRefs.length > 0 && (
                            <div>
                              <p className="mb-2 text-[11px] uppercase tracking-[0.15em] text-slate-500">
                                Related Asset Refs
                              </p>
                              <div className="flex flex-wrap gap-2">
                                {relatedAssetRefs.map((assetRef) => (
                                  <code
                                    key={`${recommendation.id}-asset-ref-${assetRef}`}
                                    className="rounded-md border border-emerald-400/20 bg-emerald-500/10 px-2 py-1 text-xs text-emerald-300"
                                  >
                                    {assetRef}
                                  </code>
                                ))}
                              </div>
                            </div>
                          )}
                          {correlationRefs.length > 0 && (
                            <div>
                              <p className="mb-2 text-[11px] uppercase tracking-[0.15em] text-slate-500">
                                Correlation Refs
                              </p>
                              <div className="flex flex-wrap gap-2">
                                {correlationRefs.map((correlationRef) => (
                                  <code
                                    key={`${recommendation.id}-correlation-ref-${correlationRef}`}
                                    className="rounded-md border border-sky-400/20 bg-sky-500/10 px-2 py-1 text-xs text-sky-300"
                                  >
                                    {correlationRef}
                                  </code>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                  {priorityFactors.length > 0 && (
                    <div>
                      <div className="mb-2 flex items-center gap-2">
                        <Sparkles className="h-4 w-4 text-indigo-300" />
                        <p className="text-xs uppercase tracking-[0.15em] text-slate-500">Priority Factors</p>
                      </div>
                      <div className="grid gap-3 xl:grid-cols-2">
                        {priorityFactors.map((factor) => (
                          <div
                            key={`${recommendation.id}-${factor.key}`}
                            className="rounded-lg border border-white/10 bg-white/5 p-3"
                          >
                            <div className="flex items-start justify-between gap-3">
                              <div>
                                <p className="text-sm font-semibold text-white">{factor.label}</p>
                                <p className="mt-1 text-xs text-slate-400">{factor.sourceBasis}</p>
                              </div>
                              <span className="rounded-full border border-indigo-400/20 bg-indigo-500/10 px-2.5 py-1 text-xs font-medium text-indigo-300">
                                {factor.score > 0 ? `+${factor.score}` : String(factor.score)}
                              </span>
                            </div>
                            <div className="mt-3 flex flex-wrap gap-2">
                              <span className="rounded-md border border-white/10 bg-slate-900/40 px-2 py-1 text-xs text-slate-300">
                                {factor.evidenceType}
                              </span>
                              <span className="rounded-md border border-white/10 bg-slate-900/40 px-2 py-1 text-xs text-slate-300">
                                {factor.formula}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="text-slate-300">
                <div className="mb-3 flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-indigo-300" />
                  <h3 className="text-lg font-semibold text-white">AI Migration Guide</h3>
                </div>
                {primaryGuide ? (
                  renderMarkdown(primaryGuide)
                ) : (
                  <p className="leading-relaxed text-slate-300">
                    Detailed migration guidance was not returned. Use the deterministic priority basis
                    and affected locations below to plan the transition.
                  </p>
                )}
              </div>

              {validationChecklist.length > 0 && (
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
                  <div className="mb-4 flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-indigo-300" />
                    <h3 className="text-lg font-semibold text-white">Validation Checklist</h3>
                  </div>
                  <ul className="space-y-2 text-sm text-slate-300">
                    {validationChecklist.map((item) => (
                      <li key={`${recommendation.id}-${item}`} className="flex items-start gap-2">
                        <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-indigo-300" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {(benchmarkNotes.length > 0 || assumptions.length > 0) && (
                <div className="grid gap-4 xl:grid-cols-2">
                  <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
                    <div className="mb-4 flex items-center gap-2">
                      <Database className="h-5 w-5 text-indigo-300" />
                      <h3 className="text-lg font-semibold text-white">Benchmark Notes</h3>
                    </div>
                    {benchmarkNotes.length > 0 ? (
                      <ul className="space-y-2 text-sm text-slate-300">
                        {benchmarkNotes.map((item) => {
                          const support = benchmarkSupport.find((entry) => entry.note === item)
                          return (
                            <li key={`${recommendation.id}-${item}`} className="flex items-start gap-2">
                              <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-indigo-300" />
                              <div>
                                <span>{item}</span>
                                {support && support.citationTitles.length > 0 && (
                                  <div className="mt-2 flex flex-wrap gap-2">
                                    {support.citationTitles.map((title) => (
                                      <span
                                        key={`${recommendation.id}-${item}-${title}`}
                                        className="rounded-full border border-amber-400/20 bg-amber-500/10 px-2.5 py-1 text-[11px] text-amber-300"
                                      >
                                        {title}
                                      </span>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </li>
                          )
                        })}
                      </ul>
                    ) : (
                      <p className="text-sm text-slate-500">Benchmark guidance was not returned.</p>
                    )}
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
                    <div className="mb-4 flex items-center gap-2">
                      <AlertTriangle className="h-5 w-5 text-indigo-300" />
                      <h3 className="text-lg font-semibold text-white">Assumptions</h3>
                    </div>
                    {assumptions.length > 0 ? (
                      <ul className="space-y-2 text-sm text-slate-300">
                        {assumptions.map((item) => (
                          <li key={`${recommendation.id}-${item}`} className="flex items-start gap-2">
                            <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-indigo-300" />
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm text-slate-500">Assumptions were not returned.</p>
                    )}
                  </div>
                </div>
              )}

              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
                <div className="mb-4 flex items-center gap-2">
                  <FileCode className="h-5 w-5 text-indigo-300" />
                  <h3 className="text-lg font-semibold text-white">Affected Code Locations</h3>
                </div>
                {affectedLocations.length > 0 ? (
                  <div className="space-y-3">
                    {affectedLocations.slice(0, 8).map((location, index) => (
                      <div
                        key={`${recommendation.id}-loc-${index}`}
                        className="rounded-lg border border-white/10 bg-white/5 p-3"
                      >
                        <p className="font-mono text-sm text-slate-100">{location.file_path}</p>
                        <p className="mt-1 text-xs text-slate-400">
                          line {location.line_start ?? '?'}
                          {location.line_end && location.line_end !== location.line_start
                            ? `-${location.line_end}`
                            : ''}
                          {location.rule_id ? ` | rule=${location.rule_id}` : ''}
                          {location.scanner_type ? ` | scanner=${location.scanner_type}` : ''}
                        </p>
                        {location.evidence_excerpt && (
                          <pre className="mt-2 overflow-x-auto whitespace-pre-wrap rounded border border-white/10 bg-slate-900/40 p-2 text-xs text-slate-300">
                            <code>{location.evidence_excerpt}</code>
                          </pre>
                        )}
                      </div>
                    ))}
                  </div>
                ) : affectedFilePaths.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {affectedFilePaths.map((path) => (
                      <code
                        key={`${recommendation.id}-${path}`}
                        className="rounded-md border border-white/10 bg-white/5 px-2 py-1 text-xs text-slate-300"
                      >
                        {path}
                      </code>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-400">
                    No concrete affected locations were returned by the current payload.
                  </p>
                )}
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
                <div className="mb-4 flex items-center gap-2">
                  <Code className="h-5 w-5 text-indigo-300" />
                  <h3 className="text-lg font-semibold text-white">Suggested Code Fixes</h3>
                </div>
                {codeFixExamples.length > 0 ? (
                  <div className="space-y-4">
                    {codeFixExamples.slice(0, 6).map((fix, index) => (
                      <div
                        key={`${recommendation.id}-fix-${index}`}
                        className="space-y-3 rounded-lg border border-white/10 bg-white/5 p-4"
                      >
                        <div className="flex items-center justify-between gap-3">
                          <p className="font-mono text-sm text-slate-100">{fix.file_path}</p>
                          <p className="text-xs text-slate-400">
                            {fix.language ? `${fix.language} | ` : ''}
                            confidence {Math.round(Math.max(0, Math.min(1, fix.confidence ?? 0)) * 100)}%
                          </p>
                        </div>
                        <p className="text-sm text-slate-300">{fix.rationale}</p>
                        <div className="grid gap-3 xl:grid-cols-2">
                          <div>
                            <p className="mb-2 text-xs uppercase tracking-[0.15em] text-rose-300">Before</p>
                            <pre className="overflow-x-auto whitespace-pre-wrap rounded border border-rose-400/20 bg-slate-900/60 p-3 text-xs text-slate-200">
                              <code>{fix.before_code}</code>
                            </pre>
                          </div>
                          <div>
                            <p className="mb-2 text-xs uppercase tracking-[0.15em] text-emerald-300">After</p>
                            <pre className="overflow-x-auto whitespace-pre-wrap rounded border border-emerald-400/20 bg-slate-900/60 p-3 text-xs text-slate-200">
                              <code>{fix.after_code}</code>
                            </pre>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-400">
                    No concrete before/after patch examples were returned by the AI response.
                  </p>
                )}
              </div>

              <div className="space-y-4 rounded-2xl border border-white/10 bg-white/[0.03] p-5">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-indigo-300" />
                  <h3 className="text-lg font-semibold text-white">Evidence</h3>
                </div>

                {!hasNistReference && (
                  <div className="rounded-xl border border-amber-400/20 bg-amber-500/10 p-4">
                    <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                      <div className="flex items-start gap-3">
                        <AlertTriangle className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-300" />
                        <div>
                          <p className="text-sm font-semibold text-amber-200">NIST citation not available</p>
                          <p className="mt-1 text-sm leading-relaxed text-amber-100/90">
                            RAG corpus is not loaded or no matching section was retrieved. Confidence is reduced.
                          </p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={handleRetryCitations}
                        disabled={!canRetryCitations || isRetrying}
                        title={canRetryCitations ? undefined : 'Backend re-run not available yet'}
                        className="inline-flex items-center justify-center gap-2 rounded-lg border border-amber-300/20 bg-white/5 px-3 py-2 text-sm font-medium text-amber-100 transition-colors hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {isRetrying ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <RefreshCw className="h-4 w-4" />
                        )}
                        Retry citations
                      </button>
                    </div>
                    {retryMessage && <p className="mt-3 text-xs text-amber-100/80">{retryMessage}</p>}
                  </div>
                )}

                {hasNistReference && (
                  <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                    <p className="mb-2 text-xs uppercase tracking-[0.2em] text-slate-500">
                      NIST Standard Reference
                    </p>
                    <p className="text-sm font-medium text-slate-100">
                      {getDisplayValue(recommendation.nistStandardReference)}
                    </p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <span className="rounded-full border border-indigo-400/20 bg-indigo-500/10 px-2.5 py-1 text-xs text-indigo-300">
                        Normative evidence {normativeCitationRows.length}
                      </span>
                      <span className="rounded-full border border-amber-400/20 bg-amber-500/10 px-2.5 py-1 text-xs text-amber-300">
                        Benchmark evidence {benchmarkCitationRows.length}
                      </span>
                      {otherCitationRows.length > 0 && (
                        <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-slate-300">
                          Other evidence {otherCitationRows.length}
                        </span>
                      )}
                    </div>
                    {normativeEvidenceCount === 0 && (
                      <p className="mt-3 text-xs text-amber-300">
                        Planning reference only. No normative excerpt is attached to this recommendation yet.
                      </p>
                    )}
                  </div>
                )}

                {citationEvidenceRows.length > 0 ? (
                  <div className="space-y-4">
                    {renderCitationGroup(
                      'Normative Evidence',
                      'Use this group for migration requirements, risk framing, and standard conformance claims.',
                      normativeCitationRows,
                    )}
                    {renderCitationGroup(
                      'Benchmark Evidence',
                      'Use this group for latency, interoperability, certificate size, and deployment tradeoff notes.',
                      benchmarkCitationRows,
                    )}
                    {renderCitationGroup(
                      'Other Evidence',
                      'Auxiliary evidence that does not clearly map to normative or benchmark guidance.',
                      otherCitationRows,
                    )}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400">
                    Supporting excerpts were not attached to this result.
                  </p>
                )}
              </div>

              <div className="space-y-4 rounded-2xl border border-white/10 bg-white/[0.03] p-5">
                <div className="flex items-center gap-2">
                  <Info className="h-5 w-5 text-indigo-300" />
                  <h3 className="text-lg font-semibold text-white">Confidence</h3>
                </div>

                <div className="space-y-2">
                  <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                    <p className="mb-2 text-xs uppercase tracking-[0.2em] text-slate-500">Analysis Status</p>
                    <div className="flex flex-wrap gap-2">
                      {analysisModeConfig ? (
                        <span className={`rounded-full border px-2.5 py-1 text-xs ${analysisModeConfig.className}`}>
                          {analysisModeConfig.label}
                        </span>
                      ) : (
                        <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-slate-300">
                          Analysis mode unknown
                        </span>
                      )}
                      <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-slate-300">
                        RAG corpus {ragCorpusLoaded ? 'loaded' : 'not loaded'}
                      </span>
                      <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-slate-300">
                        Citations {citationsAvailable ? 'available' : 'missing'}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-300">Recommendation confidence</span>
                    <span className="font-semibold text-white">
                      {confidencePercent === null ? 'Not available' : `${confidencePercent}%`}
                    </span>
                  </div>
                  <div className="h-2.5 overflow-hidden rounded-full bg-white/5">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${getConfidenceFillClass(confidencePercent)}`}
                      style={{ width: `${confidencePercent ?? 0}%` }}
                    />
                  </div>
                </div>

                <ul className="space-y-2 text-sm text-slate-300">
                  <li className="flex items-start gap-2">
                    {evidenceTotal > 0 ? (
                      <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-300" />
                    ) : (
                      <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-300" />
                    )}
                    <span>
                      Evidence strength:{' '}
                      {evidenceTotal > 0 ? `supported by ${evidenceTotal} evidence points` : 'unknown'}
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    {duplicateState === 'confirmed' ? (
                      <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-300" />
                    ) : (
                      <Info className="mt-0.5 h-4 w-4 flex-shrink-0 text-slate-400" />
                    )}
                    <span>
                      Consistency and duplicates:{' '}
                      {duplicateState === 'confirmed'
                        ? 'duplicate handling was noted in the analysis'
                        : 'unknown from current payload'}
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    {hasCitations ? (
                      <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-300" />
                    ) : (
                      <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-rose-300" />
                    )}
                    <span>
                      Citations present:{' '}
                      {hasCitations
                        ? 'supporting excerpts are attached'
                        : 'missing, which reduced confidence'}
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    {hasNistEvidence ? (
                      <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-300" />
                    ) : (
                      <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-300" />
                    )}
                    <span>
                      Standards evidence:{' '}
                      {hasNistEvidence ? 'NIST reference or citations are attached' : 'not available'}
                    </span>
                  </li>
                </ul>

                {confidenceReason && (
                  <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                    <p className="mb-2 text-xs uppercase tracking-[0.2em] text-slate-500">Confidence Reason</p>
                    <p className="text-sm text-slate-300">{confidenceReason}</p>
                  </div>
                )}
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
                <div className="mb-3 flex items-center gap-2">
                  <Info className="h-5 w-5 text-indigo-300" />
                  <h3 className="text-lg font-semibold text-white">Analysis Summary</h3>
                </div>
                <p className="text-sm leading-relaxed text-slate-300">{findingsSummary}</p>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between gap-4 border-t border-white/10 bg-white/5 p-4">
            <p className="text-xs text-slate-500">
              Generated by AI-PQC Scanner | Findings summary: {findingsSummary}
            </p>
            <button
              onClick={onClose}
              className="rounded-lg bg-gradient-to-r from-indigo-500 to-purple-600 px-6 py-2 font-semibold text-white transition-all duration-300 hover:from-indigo-600 hover:to-purple-700"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </>
  )
}
