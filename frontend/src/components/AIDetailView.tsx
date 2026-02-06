import { type Recommendation, type Priority } from '../services/recommendationService'
import { X, Sparkles, Code, AlertCircle, AlertTriangle, Info, CheckCircle2 } from 'lucide-react'
import { useEffect } from 'react'

interface AIDetailViewProps {
  recommendation: Recommendation | null
  isOpen: boolean
  onClose: () => void
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

const renderMarkdown = (text: string) => {
  const lines = text.split('\n')
  const elements: JSX.Element[] = []
  let currentCodeBlock: string[] = []
  let inCodeBlock = false
  let codeLanguage = ''

  lines.forEach((line, index) => {
    if (line.startsWith('```')) {
      if (inCodeBlock) {
        elements.push(
          <pre
            key={`code-${index}`}
            className="bg-slate-900/50 border border-white/10 rounded-lg p-4 overflow-x-auto my-4"
          >
            <code className="text-sm text-slate-200 font-mono">{currentCodeBlock.join('\n')}</code>
          </pre>
        )
        currentCodeBlock = []
        inCodeBlock = false
        codeLanguage = ''
      } else {
        codeLanguage = line.replace('```', '').trim()
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
        </h2>
      )
      return
    }

    if (line.startsWith('### ')) {
      elements.push(
        <h3 key={index} className="text-lg font-semibold text-slate-200 mt-4 mb-2">
          {line.replace('### ', '')}
        </h3>
      )
      return
    }

    if (line.startsWith('- ')) {
      elements.push(
        <li key={index} className="text-slate-300 ml-4 mb-1">
          {line.replace('- ', '')}
        </li>
      )
      return
    }

    if (line.trim() !== '') {
      elements.push(
        <p key={index} className="text-slate-300 mb-3 leading-relaxed">
          {line}
        </p>
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
      </pre>
    )
  }

  return elements
}

export const AIDetailView = ({ recommendation, isOpen, onClose }: AIDetailViewProps) => {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  if (!isOpen || !recommendation) {
    return null
  }

  const PriorityIcon = getPriorityIcon(recommendation.priority)

  return (
    <>
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 animate-in fade-in duration-200"
        onClick={onClose}
      />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
        <div
          className="bg-[#020617] border border-white/10 rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col pointer-events-auto animate-in fade-in slide-in-from-bottom-4 duration-300"
          onClick={(e) => e.stopPropagation()}
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
                      <span className="text-green-300">{recommendation.recommendedPQCAlgorithm}</span>
                    </span>
                  </div>
                  {recommendation.filePath && (
                    <code className="text-xs font-mono bg-white/5 px-2 py-1 rounded">
                      {recommendation.filePath}
                    </code>
                  )}
                  <span>Effort: {recommendation.estimatedEffort}</span>
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
            <div className="prose prose-invert max-w-none">
              <div className="bg-gradient-to-r from-indigo-500/5 to-purple-600/5 border-l-4 border-indigo-500/50 p-4 mb-6 rounded-r-lg">
                <p className="text-slate-200 text-sm leading-relaxed">
                  <strong className="text-white">AI-Generated Migration Guide</strong>
                  <br />
                  This guide has been automatically generated based on your codebase analysis. Follow
                  the steps below to migrate to post-quantum cryptography.
                </p>
              </div>

              <div className="text-slate-300">{renderMarkdown(recommendation.aiRecommendation)}</div>
            </div>
          </div>
          <div className="bg-white/5 border-t border-white/10 p-4 flex items-center justify-between">
            <p className="text-xs text-slate-500">
              Generated by AI-PQC Scanner | Context: {recommendation.context}
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



