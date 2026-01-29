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

/**
 * 리스크 레벨에 따른 아이콘 반환
 */
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

/**
 * FileNode 컴포넌트
 * T024: 재귀적 파일/폴더 노드 렌더링 및 리스크 색상 표시
 */
export const FileNode = ({ node, level = 0 }: FileNodeProps) => {
  const [isExpanded, setIsExpanded] = useState(level === 0) // 루트 레벨은 기본적으로 펼침
  const riskLevel = getRiskLevel(node.aggregatedRiskScore)
  const riskColor = getRiskColor(riskLevel)
  const RiskIcon = getRiskIcon(riskLevel)
  const isFolder = node.fileType === 'folder'
  const hasChildren = isFolder && node.children && node.children.length > 0

  // 폴더인 경우 취약점 개수 계산
  const vulnerabilityCount = isFolder ? calculateVulnerabilityCount(node) : 0

  const handleToggle = () => {
    if (isFolder && hasChildren) {
      setIsExpanded(!isExpanded)
    }
  }

  return (
    <div>
      {/* 노드 자체 */}
      <div
        className={`flex items-center gap-2 py-2 px-3 rounded-lg transition-all duration-200 hover:bg-white/5 group ${
          riskLevel !== 'SAFE' ? `${riskColor.bg} ${riskColor.border} border` : ''
        }`}
        style={{ paddingLeft: `${level * 1.5 + 0.75}rem` }}
        onClick={handleToggle}
      >
        {/* 확장/축소 아이콘 (폴더만) */}
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

        {/* 파일/폴더 아이콘 */}
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

        {/* 파일/폴더 이름 */}
        <span
          className={`flex-1 text-sm font-medium ${
            riskLevel !== 'SAFE' ? riskColor.text : 'text-slate-300'
          } group-hover:text-white transition-colors`}
        >
          {node.fileName}
        </span>

        {/* 리스크 표시 */}
        {riskLevel !== 'SAFE' && (
          <div className="flex items-center gap-2 flex-shrink-0">
            {/* 리스크 아이콘 */}
            {RiskIcon && (
              <RiskIcon className={`w-4 h-4 ${riskColor.text}`} />
            )}

            {/* 리스크 점수 */}
            <span className={`text-xs font-semibold ${riskColor.text}`}>
              {node.aggregatedRiskScore.toFixed(1)}
            </span>

            {/* 폴더인 경우 취약점 개수 배지 */}
            {isFolder && vulnerabilityCount > 0 && (
              <span
                className={`px-2 py-0.5 text-xs rounded-full ${riskColor.bg} ${riskColor.border} border ${riskColor.text}`}
              >
                {vulnerabilityCount} {vulnerabilityCount === 1 ? 'issue' : 'issues'}
              </span>
            )}
          </div>
        )}

        {/* SAFE인 경우에도 폴더면 취약점 개수 표시 (0이 아닌 경우) */}
        {riskLevel === 'SAFE' && isFolder && vulnerabilityCount > 0 && (
          <span className="px-2 py-0.5 text-xs rounded-full bg-slate-500/10 border border-slate-500/30 text-slate-400">
            {vulnerabilityCount} {vulnerabilityCount === 1 ? 'issue' : 'issues'}
          </span>
        )}
      </div>

      {/* 자식 노드들 (폴더가 펼쳐져 있을 때) */}
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
