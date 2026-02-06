import { useState } from 'react'
import {
  Folder,
  FileCode,
  ChevronRight,
  ChevronDown,
  AlertCircle,
  AlertTriangle,
  Info,
  CheckCircle2,
} from 'lucide-react'
import {
  type RepositoryFile,
  getRiskLevel,
  getRiskColor,
  calculateVulnerabilityCount,
} from '../services/heatmapService'

interface FileNodeProps {
  node: RepositoryFile
  level?: number
}

const getRiskIcon = (riskLevel: ReturnType<typeof getRiskLevel>) => {
  switch (riskLevel) {
    case 'CRITICAL':
      return AlertCircle
    case 'HIGH':
      return AlertTriangle
    case 'MEDIUM':
      return Info
    case 'LOW':
      return CheckCircle2
    case 'SAFE':
      return null
  }
}

export const FileNode = ({ node, level = 0 }: FileNodeProps) => {
  const [isExpanded, setIsExpanded] = useState(level === 0)
  const riskLevel = getRiskLevel(node.aggregatedRiskScore)
  const riskColor = getRiskColor(riskLevel)
  const RiskIcon = getRiskIcon(riskLevel)
  const isFolder = node.fileType === 'folder'
  const hasChildren = isFolder && node.children && node.children.length > 0

  const vulnerabilityCount = isFolder ? calculateVulnerabilityCount(node) : 0

  const handleToggle = () => {
    if (isFolder && hasChildren) {
      setIsExpanded(!isExpanded)
    }
  }

  return (
    <div>
      <div
        className={`flex items-center gap-2 py-2 px-3 rounded-lg transition-all duration-200 hover:bg-white/5 group ${
          riskLevel !== 'SAFE' ? `${riskColor.bg} ${riskColor.border} border` : ''
        }`}
        style={{ paddingLeft: `${level * 1.5 + 0.75}rem` }}
        onClick={handleToggle}
      >
        {isFolder ? (
          <div className="flex-shrink-0 w-4 h-4 flex items-center justify-center">
            {hasChildren ? (
              isExpanded ? (
                <ChevronDown className="w-4 h-4 text-slate-400" />
              ) : (
                <ChevronRight className="w-4 h-4 text-slate-400" />
              )
            ) : (
              <div className="w-4 h-4" />
            )}
          </div>
        ) : (
          <div className="flex-shrink-0 w-4 h-4" />
        )}
        <div className="flex-shrink-0">
          {isFolder ? (
            <Folder
              className={`w-5 h-5 ${
                riskLevel !== 'SAFE' ? riskColor.text : 'text-slate-400'
              }`}
            />
          ) : (
            <FileCode
              className={`w-5 h-5 ${
                riskLevel !== 'SAFE' ? riskColor.text : 'text-slate-400'
              }`}
            />
          )}
        </div>
        <span
          className={`flex-1 text-sm font-medium ${
            riskLevel !== 'SAFE' ? riskColor.text : 'text-slate-300'
          } group-hover:text-white transition-colors`}
        >
          {node.fileName}
        </span>
        {riskLevel !== 'SAFE' && (
          <div className="flex items-center gap-2 flex-shrink-0">
            {RiskIcon && (
              <RiskIcon className={`w-4 h-4 ${riskColor.text}`} />
            )}
            <span className={`text-xs font-semibold ${riskColor.text}`}>
              {node.aggregatedRiskScore.toFixed(1)}
            </span>
            {isFolder && vulnerabilityCount > 0 && (
              <span
                className={`px-2 py-0.5 text-xs rounded-full ${riskColor.bg} ${riskColor.border} border ${riskColor.text}`}
              >
                {vulnerabilityCount} {vulnerabilityCount === 1 ? 'issue' : 'issues'}
              </span>
            )}
          </div>
        )}
        {riskLevel === 'SAFE' && isFolder && vulnerabilityCount > 0 && (
          <span className="px-2 py-0.5 text-xs rounded-full bg-slate-500/10 border border-slate-500/30 text-slate-400">
            {vulnerabilityCount} {vulnerabilityCount === 1 ? 'issue' : 'issues'}
          </span>
        )}
      </div>
      {isFolder && hasChildren && isExpanded && (
        <div className="mt-1">
          {node.children!.map((child, index) => (
            <FileNode key={`${child.filePath}-${index}`} node={child} level={level + 1} />
          ))}
        </div>
      )}
    </div>
  )
}


