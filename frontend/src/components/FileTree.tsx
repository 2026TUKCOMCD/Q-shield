import { type HeatmapResponse } from '../services/heatmapService'
import { FileNode } from './FileNode'
import { FileCode } from 'lucide-react'

interface FileTreeProps {
  data: HeatmapResponse
}

/**
 * FileTree 컴포넌트
 * T023: 파일 트리 레이아웃 표시 컴포넌트
 */
export const FileTree = ({ data }: FileTreeProps) => {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-12 text-center">
        <FileCode className="w-12 h-12 mx-auto mb-4 text-slate-400" />
        <p className="text-slate-300 text-lg mb-2 font-medium">No repository data found</p>
        <p className="text-slate-500 text-sm">The heatmap data is empty or unavailable.</p>
      </div>
    )
  }

  return (
    <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-6 overflow-x-auto">
      <div className="min-w-full">
        {data.map((node, index) => (
          <FileNode key={`${node.filePath}-${index}`} node={node} level={0} />
        ))}
      </div>
    </div>
  )
}
