import { useMemo } from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'
import { AlertTriangle, CheckCircle2 } from 'lucide-react'

interface PqcReadinessGaugeProps {
  score: number // 0.0-10.0
}

/**
 * PQC Readiness Gauge 컴포넌트
 * Premium Security Dashboard 스타일 Donut Gauge (recharts 사용)
 */
export const PqcReadinessGauge = ({ score }: PqcReadinessGaugeProps) => {
  // 0.0-10.0 스케일을 0-100으로 변환
  const percentage = useMemo(() => {
    return Math.min(100, Math.max(0, (score / 10) * 100))
  }, [score])

  // 동적 색상 결정 (0-40: Red, 41-70: Orange, 71-100: Green)
  const getColor = (percentage: number) => {
    if (percentage >= 71) return { color: '#2ECC40', label: 'Safe' } // Emerald Green
    if (percentage >= 41) return { color: '#FF851B', label: 'Warning' } // Orange
    return { color: '#FF4136', label: 'Critical' } // Bright Red
  }

  const colorConfig = getColor(percentage)

  // 게이지 데이터 생성 (recharts PieChart용)
  const gaugeData = useMemo(() => {
    const remaining = 100 - percentage
    return [
      { name: 'Progress', value: percentage, fill: colorConfig.color },
      { name: 'Remaining', value: remaining, fill: 'transparent' },
    ]
  }, [percentage, colorConfig.color])

  // 상태 아이콘
  const StatusIcon = useMemo(() => {
    if (percentage >= 71) return CheckCircle2
    return AlertTriangle
  }, [percentage])

  return (
    <div className="flex flex-col items-center justify-center p-8 bg-white/5 backdrop-blur-md border border-white/10 rounded-xl">
      {/* Gauge Container */}
      <div className="relative w-full max-w-lg" style={{ height: '320px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            {/* Background Track - Full Range (Dark Gray) */}
            <Pie
              data={[{ name: 'Background', value: 100 }]}
              dataKey="value"
              cx="50%"
              cy="50%"
              startAngle={210}
              endAngle={-30}
              innerRadius="75%"
              outerRadius="100%"
              fill="rgba(255, 255, 255, 0.05)"
              stroke="none"
              isAnimationActive={false}
            />
            {/* Progress Track - Active Score */}
            <Pie
              data={gaugeData}
              dataKey="value"
              cx="50%"
              cy="50%"
              startAngle={210}
              endAngle={-30}
              innerRadius="75%"
              outerRadius="100%"
              cornerRadius={10}
              stroke="none"
              animationDuration={1000}
              animationBegin={0}
            >
              {gaugeData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.fill}
                  style={{
                    filter: entry.fill !== 'transparent' ? `drop-shadow(0 0 6px ${entry.fill}40)` : 'none',
                  }}
                />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>

        {/* Center Content - Absolutely Positioned */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <div className="text-center px-4">
            {/* Large Score */}
            <div
              className="text-5xl font-bold mb-1 transition-colors duration-500"
              style={{ color: colorConfig.color }}
            >
              {percentage.toFixed(0)}
            </div>
            {/* PQC Readiness Label */}
            <div className="text-xs text-slate-400 mb-2 uppercase tracking-widest font-medium">
              PQC Readiness
            </div>
            {/* Status Badge */}
            <div className="flex items-center gap-2 justify-center mb-4">
              <div
                className="px-2.5 py-1 rounded-full flex items-center gap-1.5"
                style={{
                  backgroundColor: `${colorConfig.color}15`,
                  border: `1px solid ${colorConfig.color}40`,
                }}
              >
                <StatusIcon
                  className="w-3.5 h-3.5"
                  style={{ color: colorConfig.color }}
                />
                <span
                  className="text-xs font-semibold"
                  style={{ color: colorConfig.color }}
                >
                  {colorConfig.label}
                </span>
              </div>
            </div>
            {/* Overall Score */}
            <div className="pt-3 border-t border-white/10">
              <div className="text-xs text-slate-500 mb-0.5">Overall Score</div>
              <div className="text-lg font-semibold text-white">
                {score.toFixed(1)} / 10.0
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
