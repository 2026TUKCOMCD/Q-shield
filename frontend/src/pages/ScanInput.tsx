import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ScanForm } from '../components/ScanForm'
import { type InitiateScanResponse } from '../services/scanService'
import { logInfo } from '../utils/logger'
import { Search, Shield, Zap, CheckCircle2 } from 'lucide-react'

export const ScanInput = () => {
  const navigate = useNavigate()
  const [success, setSuccess] = useState(false)
  const [successUuid, setSuccessUuid] = useState<string | null>(null)

  const handleScanInitiated = (response: InitiateScanResponse) => {
    logInfo('Scan initiated successfully', { uuid: response.uuid })
    setSuccess(true)
    setSuccessUuid(response.uuid)

    setTimeout(() => {
      navigate('/scans/history')
    }, 2500)
  }

  const handleError = (_message: string) => {
    setSuccess(false)
    setSuccessUuid(null)
  }

  return (
    <div className="min-h-screen bg-[#020617] text-white">
      <div className="fixed inset-0 bg-gradient-to-br from-slate-900 via-purple-900/20 to-slate-900 pointer-events-none" />
      <div className="fixed inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(99,102,241,0.1),transparent_50%)] pointer-events-none" />

      <div className="relative z-10 ml-0 md:ml-64 p-4 md:p-8">
        <div className="max-w-6xl mx-auto space-y-12">
          <div className="space-y-4 animate-in fade-in duration-700">
            <h1 className="text-5xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-indigo-400 bg-clip-text text-transparent">
              PQC Security Scanner
            </h1>
            <p className="text-slate-400 text-lg max-w-2xl">
              Start static analysis for post-quantum cryptography migration readiness.
            </p>
          </div>

          <div className="relative animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100">
            <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500/30 via-purple-500/30 to-indigo-500/30 rounded-2xl blur-xl opacity-50" />

            <div className="relative bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-8 shadow-2xl">
              <div className="flex items-center gap-4 mb-8">
                <div className="p-3 bg-gradient-to-br from-indigo-500/20 to-purple-600/20 rounded-xl border border-indigo-500/30">
                  <Search className="w-6 h-6 text-indigo-400" />
                </div>
                <div>
                  <h2 className="text-2xl font-semibold text-white">New Analysis</h2>
                  <p className="text-sm text-slate-400 uppercase tracking-wider mt-1">
                    Enter the repository URL for analysis.
                  </p>
                </div>
              </div>

              {success && successUuid && (
                <div className="mb-6 p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-lg flex items-center gap-3 text-emerald-400 animate-in zoom-in-95 duration-300">
                  <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm font-medium">Scan started successfully.</p>
                    <p className="text-xs text-emerald-400/70 mt-1">UUID: {successUuid}</p>
                  </div>
                </div>
              )}

              <ScanForm
                onScanInitiated={handleScanInitiated}
                onError={handleError}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-200">
            {[
              {
                icon: Shield,
                title: 'Algorithm Detection',
                description: 'Detects weak cryptographic algorithms such as RSA-1024 and SHA-1.',
                gradient: 'from-blue-500/20 to-cyan-500/20',
                borderColor: 'border-blue-500/30',
                iconColor: 'text-blue-400',
              },
              {
                icon: Search,
                title: 'Risk Scoring',
                description: 'Calculates migration risk based on post-quantum transition urgency.',
                gradient: 'from-purple-500/20 to-pink-500/20',
                borderColor: 'border-purple-500/30',
                iconColor: 'text-purple-400',
              },
              {
                icon: Zap,
                title: 'Fast AST Scan',
                description: 'Performs AST-based analysis for accurate and stable results.',
                gradient: 'from-indigo-500/20 to-purple-500/20',
                borderColor: 'border-indigo-500/30',
                iconColor: 'text-indigo-400',
              },
            ].map((feature, idx) => {
              const Icon = feature.icon
              return (
                <div
                  key={idx}
                  className="group relative bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-6 hover:bg-white/10 hover:border-white/20 transition-all duration-300 hover:-translate-y-1"
                >
                  <div
                    className={`w-12 h-12 bg-gradient-to-br ${feature.gradient} ${feature.borderColor} border rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}
                  >
                    <Icon className={`w-6 h-6 ${feature.iconColor}`} />
                  </div>
                  <h3 className="text-white font-semibold mb-2">{feature.title}</h3>
                  <p className="text-sm text-slate-400 leading-relaxed">{feature.description}</p>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
