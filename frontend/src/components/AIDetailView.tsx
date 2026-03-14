import { type ReactNode, useEffect, useState } from 'react'
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Code,
  Info,
  Loader2,
  RefreshCw,
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
            className="bg-slate-900/50 border border-white/10 rounded-lg p-4 overflow-x-auto my-4"
          >
            <code className="text-sm text-slate-200 font-mono">{currentCodeBlock.join('\n')}</code>
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
        <h2 key={index} className="text-xl font-bold text-white mt-6 mb-3">
          {line.replace('## ', '')}
        </h2>,
      )
      return
    }

    if (line.startsWith('### ')) {
      elements.push(
        <h3 key={index} className="text-lg font-semibold text-slate-200 mt-4 mb-2">
          {line.replace('### ', '')}
        </h3>,
      )
      return
    }

    if (line.startsWith('- ')) {
      elements.push(
        <li key={index} className="text-slate-300 ml-4 mb-1">
          {line.replace('- ', '')}
        </li>,
      )
      return
    }

    if (line.trim() !== '') {
      elements.push(
        <p key={index} className="text-slate-300 mb-3 leading-relaxed">
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
        className="bg-slate-900/50 border border-white/10 rounded-lg p-4 overflow-x-auto my-4"
      >
        <code className="text-sm text-slate-200 font-mono">{currentCodeBlock.join('\n')}</code>
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
  const confidencePercent =
    recommendation.confidence === undefined
      ? null
      : Math.round(Math.max(0, Math.min(1, recommendation.confidence)) * 100)
  const primaryGuide = extractPrimaryGuide(recommendation.aiRecommendation)
  const evidenceCounts = getEvidenceCounts(recommendation)
  const evidenceTotal = getEvidenceTotal(evidenceCounts)
  const findingsSummary = getDisplayValue(recommendation.analysisSummary || recommendation.context)
  const duplicateSignal = `${recommendation.analysisSummary ?? ''} ${recommendation.context ?? ''}`.toLowerCase()
  const duplicateState =
    duplicateSignal.includes('dedup') || duplicateSignal.includes('duplicate') ? 'confirmed' : 'unknown'
  const affectedLocations = recommendation.affectedLocations ?? []
  const codeFixExamples = recommendation.codeFixExamples ?? []
  const citationEvidenceRows = (recommendation.citations ?? []).map((citation) => {
    const sectionText = hasMeaningfulValue(citation.section)
      ? citation.section.trim()
      : citation.page
        ? `page ${citation.page}`
        : 'Section not available'
    const pageText = citation.page ? ` • p.${citation.page}` : ''
    return {
      key: `${citation.doc_id}:${citation.page ?? 'na'}:${sectionText}`,
      title: getDisplayValue(citation.title, 'NIST citation'),
      location: `${sectionText}${pageText}`,
    }
  })
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

  return (
    <>
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 animate-in fade-in duration-200"
        onClick={onClose}
      />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
        <div
          className="bg-[#020617] border border-white/10 rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col pointer-events-auto animate-in fade-in slide-in-from-bottom-4 duration-300"
          onClick={(event) => event.stopPropagation()}
        >
          <div className="bg-gradient-to-r from-indigo-500/10 to-purple-600/10 border-b border-white/10 p-6">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 bg-gradient-to-br from-indigo-500/20 to-purple-600/20 rounded-lg border border-indigo-500/30">
                    <Sparkles className="w-5 h-5 text-indigo-400" />
                  </div>
                  <div className="flex items-center gap-2">
                    <PriorityIcon className="w-5 h-5 text-indigo-400" />
                    <span className="px-3 py-1 bg-indigo-500/10 border border-indigo-500/30 rounded-full text-sm text-indigo-400 font-medium">
                      {recommendation.priority}
                    </span>
                  </div>
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">{recommendation.issueName}</h2>
                <div className="flex flex-wrap items-center gap-4 text-sm text-slate-400">
                  <div className="flex items-center gap-2">
                    <Code className="w-4 h-4" />
                    <span>
                      <span className="text-red-300">{recommendation.targetAlgorithm}</span>
                      {' -> '}
                      <span className="text-green-300">
                        {getDisplayValue(recommendation.recommendedPQCAlgorithm, '—')}
                      </span>
                    </span>
                  </div>
                  {recommendation.filePath && (
                    <code className="text-xs font-mono bg-white/5 px-2 py-1 rounded">
                      {recommendation.filePath}
                    </code>
                  )}
                  <span>Effort: {getDisplayValue(recommendation.estimatedEffort, '—')}</span>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-white/10 rounded-lg transition-colors text-slate-400 hover:text-white flex-shrink-0"
                aria-label="Close"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-6">
            <div className="space-y-6">
              <div className="grid grid-cols-2 xl:grid-cols-5 gap-3">
                <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                  <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500 mb-2">
                    Target Algorithm
                  </p>
                  <p className="text-sm font-semibold text-red-300">{recommendation.targetAlgorithm}</p>
                </div>
                <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                  <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500 mb-2">
                    Recommended PQC
                  </p>
                  <p
                    className="text-sm font-semibold text-green-300"
                    title={
                      hasMeaningfulValue(recommendation.recommendedPQCAlgorithm)
                        ? undefined
                        : 'A concrete replacement was not returned by the backend.'
                    }
                  >
                    {getDisplayValue(recommendation.recommendedPQCAlgorithm, '—')}
                  </p>
                </div>
                <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                  <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500 mb-2">Effort</p>
                  <p className="text-sm font-semibold text-slate-200">
                    {getDisplayValue(recommendation.estimatedEffort, '—')}
                  </p>
                </div>
                <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                  <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500 mb-2">NIST</p>
                  <p
                    className={`text-sm font-semibold ${hasNistEvidence ? 'text-emerald-300' : 'text-amber-300'}`}
                  >
                    {hasNistEvidence ? 'Available' : 'Missing'}
                  </p>
                </div>
                <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                  <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500 mb-2">Confidence</p>
                  <p className="text-sm font-semibold text-slate-200">
                    {confidencePercent === null ? '—' : `${confidencePercent}%`}
                  </p>
                </div>
              </div>

              <div className="bg-gradient-to-r from-indigo-500/5 to-purple-600/5 border-l-4 border-indigo-500/50 p-4 rounded-r-lg">
                <p className="text-slate-200 text-sm leading-relaxed">
                  <strong className="text-white">AI-Generated Migration Guide</strong>
                  <br />
                  This guidance is based on the scan output and the current AI analysis. Use the
                  affected locations and suggested code fixes below to build your migration plan.
                </p>
              </div>

              <div className="text-slate-300">
                {primaryGuide ? (
                  renderMarkdown(primaryGuide)
                ) : (
                  <p className="text-slate-300 leading-relaxed">
                    Detailed migration guidance was not returned. Use the affected locations and
                    suggested code fixes below as the starting point for implementation planning.
                  </p>
                )}
              </div>

              <div className="bg-white/[0.03] border border-white/10 rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-4">
                  <Code className="w-5 h-5 text-indigo-300" />
                  <h3 className="text-lg font-semibold text-white">Affected Code Locations</h3>
                </div>
                {affectedLocations.length > 0 ? (
                  <div className="space-y-3">
                    {affectedLocations.slice(0, 8).map((location, index) => (
                      <div key={`${recommendation.id}-loc-${index}`} className="rounded-lg border border-white/10 bg-white/5 p-3">
                        <p className="text-sm text-slate-100 font-mono">{location.file_path}</p>
                        <p className="text-xs text-slate-400 mt-1">
                          line {location.line_start ?? '?'}{location.line_end && location.line_end !== location.line_start ? `-${location.line_end}` : ''}
                          {location.rule_id ? ` | rule=${location.rule_id}` : ''}
                          {location.scanner_type ? ` | scanner=${location.scanner_type}` : ''}
                        </p>
                        {location.evidence_excerpt && (
                          <pre className="mt-2 whitespace-pre-wrap text-xs text-slate-300 bg-slate-900/40 border border-white/10 rounded p-2 overflow-x-auto">
                            <code>{location.evidence_excerpt}</code>
                          </pre>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-400">No concrete affected locations were returned by the AI response.</p>
                )}
              </div>

              <div className="bg-white/[0.03] border border-white/10 rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-4">
                  <Code className="w-5 h-5 text-indigo-300" />
                  <h3 className="text-lg font-semibold text-white">Suggested Code Fixes</h3>
                </div>
                {codeFixExamples.length > 0 ? (
                  <div className="space-y-4">
                    {codeFixExamples.slice(0, 6).map((fix, index) => (
                      <div key={`${recommendation.id}-fix-${index}`} className="rounded-lg border border-white/10 bg-white/5 p-4 space-y-3">
                        <div className="flex items-center justify-between gap-3">
                          <p className="text-sm text-slate-100 font-mono">{fix.file_path}</p>
                          <p className="text-xs text-slate-400">
                            {fix.language ? `${fix.language} | ` : ''}confidence {Math.round(Math.max(0, Math.min(1, fix.confidence ?? 0)) * 100)}%
                          </p>
                        </div>
                        <p className="text-sm text-slate-300">{fix.rationale}</p>
                        <div className="grid gap-3 xl:grid-cols-2">
                          <div>
                            <p className="text-xs uppercase tracking-[0.15em] text-rose-300 mb-2">Before</p>
                            <pre className="whitespace-pre-wrap text-xs text-slate-200 bg-slate-900/60 border border-rose-400/20 rounded p-3 overflow-x-auto">
                              <code>{fix.before_code}</code>
                            </pre>
                          </div>
                          <div>
                            <p className="text-xs uppercase tracking-[0.15em] text-emerald-300 mb-2">After</p>
                            <pre className="whitespace-pre-wrap text-xs text-slate-200 bg-slate-900/60 border border-emerald-400/20 rounded p-3 overflow-x-auto">
                              <code>{fix.after_code}</code>
                            </pre>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-400">No concrete before/after patch examples were returned by the AI response.</p>
                )}
              </div>

              <div className="bg-white/[0.03] border border-white/10 rounded-2xl p-5 space-y-4">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-indigo-300" />
                  <h3 className="text-lg font-semibold text-white">NIST Evidence</h3>
                </div>

                {!hasNistReference && (
                  <div className="rounded-xl border border-amber-400/20 bg-amber-500/10 p-4">
                    <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                      <div className="flex items-start gap-3">
                        <AlertTriangle className="w-5 h-5 text-amber-300 mt-0.5 flex-shrink-0" />
                        <div>
                          <p className="text-sm font-semibold text-amber-200">
                            NIST citation not available
                          </p>
                          <p className="text-sm text-amber-100/90 mt-1 leading-relaxed">
                            RAG corpus is not loaded or no matching section was retrieved. Confidence
                            is reduced.
                          </p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={handleRetryCitations}
                        disabled={!canRetryCitations || isRetrying}
                        title={
                          canRetryCitations ? undefined : 'Backend re-run not available yet'
                        }
                        className="inline-flex items-center justify-center gap-2 rounded-lg border border-amber-300/20 bg-white/5 px-3 py-2 text-sm font-medium text-amber-100 transition-colors hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {isRetrying ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <RefreshCw className="w-4 h-4" />
                        )}
                        Retry citations
                      </button>
                    </div>
                    {retryMessage && <p className="mt-3 text-xs text-amber-100/80">{retryMessage}</p>}
                  </div>
                )}

                {hasNistReference && (
                  <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-500 mb-2">
                      NIST Standard Reference
                    </p>
                    <p className="text-sm font-medium text-slate-100">
                      {getDisplayValue(recommendation.nistStandardReference)}
                    </p>
                    {citationEvidenceRows.length > 0 ? (
                      <div className="mt-3 space-y-3">
                        {citationEvidenceRows.map((row) => (
                          <div
                            key={row.key}
                            className="rounded-lg border border-white/10 bg-white/5 p-3"
                          >
                            <p className="text-sm font-semibold text-white">{row.title}</p>
                            <p className="mt-1 text-xs text-indigo-300">{row.location}</p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="mt-2 text-xs text-slate-400">
                        Supporting excerpts were not attached to this result.
                      </p>
                    )}
                  </div>
                )}
              </div>

              <div className="bg-white/[0.03] border border-white/10 rounded-2xl p-5 space-y-4">
                <div className="flex items-center gap-2">
                  <Info className="w-5 h-5 text-indigo-300" />
                  <h3 className="text-lg font-semibold text-white">Confidence</h3>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-300">Recommendation confidence</span>
                    <span className="font-semibold text-white">
                      {confidencePercent === null ? 'Not available' : `${confidencePercent}%`}
                    </span>
                  </div>
                  <div className="h-2.5 rounded-full bg-white/5 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${getConfidenceFillClass(confidencePercent)}`}
                      style={{ width: `${confidencePercent ?? 0}%` }}
                    />
                  </div>
                </div>

                <ul className="space-y-2 text-sm text-slate-300">
                  <li className="flex items-start gap-2">
                    {evidenceCounts.length > 0 ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-300 mt-0.5 flex-shrink-0" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-amber-300 mt-0.5 flex-shrink-0" />
                    )}
                    <span>
                      Evidence strength:{' '}
                      {evidenceCounts.length > 0
                        ? `${evidenceTotal > 0 ? 'supported by current findings' : 'counts returned'}`
                        : 'unknown'}
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    {duplicateState === 'confirmed' ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-300 mt-0.5 flex-shrink-0" />
                    ) : (
                      <Info className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
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
                      <CheckCircle2 className="w-4 h-4 text-emerald-300 mt-0.5 flex-shrink-0" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-rose-300 mt-0.5 flex-shrink-0" />
                    )}
                    <span>
                      Citations present:{' '}
                      {hasCitations
                        ? 'supporting excerpts are attached'
                        : 'missing, which reduced confidence'}
                    </span>
                  </li>
                </ul>

                <div className="rounded-xl border border-white/10 bg-white/5 p-4 space-y-1">
                  <p className="text-sm text-slate-200">
                    Evidence:{' '}
                    {evidenceCounts.length > 0
                      ? evidenceCounts.slice(0, 3).join(', ')
                      : 'Counts not available'}
                  </p>
                  {!hasCitations && (
                    <p className="text-sm text-slate-400">Citations missing, so confidence is reduced</p>
                  )}
                  {!hasCitations && (
                    <p className="text-xs text-slate-500">
                      Load the RAG corpus and retry citations to increase confidence.
                    </p>
                  )}
                </div>
              </div>

              <div className="bg-white/[0.03] border border-white/10 rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Info className="w-5 h-5 text-indigo-300" />
                  <h3 className="text-lg font-semibold text-white">Analysis Summary</h3>
                </div>
                <p className="text-sm leading-relaxed text-slate-300">{findingsSummary}</p>
              </div>
            </div>
          </div>
          <div className="bg-white/5 border-t border-white/10 p-4 flex items-center justify-between gap-4">
            <p className="text-xs text-slate-500">
              Generated by AI-PQC Scanner | Findings summary: {findingsSummary}
            </p>
            <button
              onClick={onClose}
              className="px-6 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-semibold rounded-lg transition-all duration-300"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </>
  )
}
