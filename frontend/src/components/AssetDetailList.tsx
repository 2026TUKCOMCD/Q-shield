import { type AssetDetail } from '../services/inventoryService'
import {
  FileCode,
  Key,
  Shield,
  Code,
  AlertCircle,
  Sparkles,
  ExternalLink,
} from 'lucide-react'

interface AssetDetailListProps {
  asset: AssetDetail
}

const getRiskColor = (riskScore: number) => {
  if (riskScore >= 8.0)
    return {
      color: 'text-red-400',
      bg: 'bg-red-500/10',
      border: 'border-red-500/30',
      label: 'Critical',
    }
  if (riskScore >= 5.0)
    return {
      color: 'text-orange-400',
      bg: 'bg-orange-500/10',
      border: 'border-orange-500/30',
      label: 'High',
    }
  return {
    color: 'text-yellow-400',
    bg: 'bg-yellow-500/10',
    border: 'border-yellow-500/30',
    label: 'Medium',
  }
}

const getComplexityColor = (complexity?: string) => {
  switch (complexity) {
    case 'High':
      return 'text-red-400'
    case 'Medium':
      return 'text-orange-400'
    case 'Low':
      return 'text-green-400'
    default:
      return 'text-slate-400'
  }
}

const renderCodeSnippet = (code: string, lineNumbers: number[], startLine?: number) => {
  const lines = code.split('\n')
  const lineNumberSet = new Set(lineNumbers)
  const baseLine = startLine && startLine > 0 ? startLine : 1

  return (
    <div className="bg-slate-900/50 border border-white/10 rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <pre className="p-4 text-sm">
          <code className="text-slate-200 font-mono">
            {lines.map((line, index) => {
              const lineNum = baseLine + index
              const isHighlighted = lineNumberSet.has(lineNum)

              return (
                <div
                  key={index}
                  className={`flex ${
                    isHighlighted ? 'bg-yellow-500/10 border-l-2 border-yellow-500/50' : ''
                  }`}
                >
                  <span className="text-slate-500 pr-4 select-none w-12 text-right">
                    {lineNum}
                  </span>
                  <span className={`flex-1 ${isHighlighted ? 'text-yellow-300' : 'text-slate-300'}`}>
                    {line || ' '}
                  </span>
                </div>
              )
            })}
          </code>
        </pre>
      </div>
    </div>
  )
}

export const AssetDetailList = ({ asset }: AssetDetailListProps) => {
  const riskConfig = getRiskColor(asset.riskScore)

  return (
    <div className="space-y-6">
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-gradient-to-br from-indigo-500/20 to-purple-600/20 rounded-lg border border-indigo-500/30">
            <Shield className="w-5 h-5 text-indigo-400" />
          </div>
          <h2 className="text-2xl font-semibold text-white">Technical Specifications</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <FileCode className="w-4 h-4" />
              <span>Algorithm Type</span>
            </div>
            <p className="text-lg font-semibold text-white">{asset.algorithmType}</p>
          </div>
          {asset.keySize && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <Key className="w-4 h-4" />
                <span>Key Size</span>
              </div>
              <p className="text-lg font-semibold text-white">{asset.keySize} bits</p>
            </div>
          )}
          {asset.modeOfOperation && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <Code className="w-4 h-4" />
                <span>Mode of Operation</span>
              </div>
              <p className="text-lg font-semibold text-white">{asset.modeOfOperation}</p>
            </div>
          )}
          {asset.implementation && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <Shield className="w-4 h-4" />
                <span>Implementation</span>
              </div>
              <p className="text-lg font-semibold text-white">{asset.implementation}</p>
            </div>
          )}
          {asset.standard && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <FileCode className="w-4 h-4" />
                <span>Standard</span>
              </div>
              <p className="text-lg font-semibold text-white">{asset.standard}</p>
            </div>
          )}
          {asset.paddingScheme && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <Key className="w-4 h-4" />
                <span>Padding Scheme</span>
              </div>
              <p className="text-lg font-semibold text-white">{asset.paddingScheme}</p>
            </div>
          )}
          {asset.keyDerivationFunction && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <Key className="w-4 h-4" />
                <span>Key Derivation Function</span>
              </div>
              <p className="text-lg font-semibold text-white">{asset.keyDerivationFunction}</p>
            </div>
          )}
        </div>
      </div>
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-gradient-to-br from-indigo-500/20 to-purple-600/20 rounded-lg border border-indigo-500/30">
            <FileCode className="w-5 h-5 text-indigo-400" />
          </div>
          <h2 className="text-2xl font-semibold text-white">Context & Location</h2>
        </div>

        <div className="space-y-4">
          <div>
            <div className="text-sm text-slate-400 mb-2">File Path</div>
            <code className="text-sm text-slate-300 font-mono bg-white/5 px-3 py-2 rounded block">
              {asset.filePath}
            </code>
          </div>
          <div>
            <div className="text-sm text-slate-400 mb-2">Line Numbers</div>
            <div className="flex flex-wrap gap-2">
              {asset.lineNumbers.map((line, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 text-sm bg-yellow-500/10 border border-yellow-500/30 text-yellow-300 rounded font-mono"
                >
                  {line}
                </span>
              ))}
            </div>
          </div>
          {asset.detectedPattern && (
            <div>
              <div className="text-sm text-slate-400 mb-2">Detected Pattern</div>
              <code className="text-sm text-slate-300 font-mono bg-white/5 px-3 py-2 rounded block">
                {asset.detectedPattern}
              </code>
            </div>
          )}
          {asset.codeSnippet && (
            <div>
              <div className="text-sm text-slate-400 mb-2">Code Snippet</div>
              {renderCodeSnippet(asset.codeSnippet, asset.lineNumbers, asset.codeSnippetStartLine)}
            </div>
          )}
        </div>
      </div>
      {asset.suggestedPQCAlternatives && asset.suggestedPQCAlternatives.length > 0 && (
        <div className="bg-gradient-to-r from-indigo-500/10 to-purple-600/10 backdrop-blur-md border border-indigo-500/30 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-gradient-to-br from-indigo-500/20 to-purple-600/20 rounded-lg border border-indigo-500/30">
              <Sparkles className="w-5 h-5 text-indigo-400" />
            </div>
            <h2 className="text-2xl font-semibold text-white">AI-Suggested PQC Alternatives</h2>
          </div>

          <div className="space-y-4">
            <div>
              <div className="text-sm text-slate-400 mb-3">Recommended Algorithms</div>
              <div className="flex flex-wrap gap-3">
                {asset.suggestedPQCAlternatives.map((alt, idx) => (
                  <div
                    key={idx}
                    className="px-4 py-2 bg-green-500/10 border border-green-500/30 rounded-lg flex items-center gap-2"
                  >
                    <Sparkles className="w-4 h-4 text-green-400" />
                    <span className="text-green-300 font-medium">{alt}</span>
                  </div>
                ))}
              </div>
            </div>
            {asset.migrationComplexity && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-slate-400 mb-2">Migration Complexity</div>
                  <div
                    className={`text-lg font-semibold ${getComplexityColor(asset.migrationComplexity)}`}
                  >
                    {asset.migrationComplexity}
                  </div>
                </div>
                {asset.estimatedEffort && (
                  <div>
                    <div className="text-sm text-slate-400 mb-2">Estimated Effort</div>
                    <div className="text-lg font-semibold text-white">{asset.estimatedEffort}</div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}


