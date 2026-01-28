import { Link, useLocation } from 'react-router-dom'
import { Scan, History, Shield } from 'lucide-react'

/**
 * 사이드바 네비게이션 컴포넌트
 */
export const Sidebar = () => {
  const location = useLocation()

  const navItems = [
    {
      path: '/scans/new',
      label: 'New Scan',
      icon: Scan,
    },
    {
      path: '/scans/history',
      label: 'History',
      icon: History,
    },
  ]

  return (
    <div className="fixed left-0 top-0 h-full w-64 bg-slate-900/80 backdrop-blur-md border-r border-white/10 z-50 hidden md:block">
      <div className="flex flex-col h-full">
        {/* Logo/Brand */}
        <div className="p-6 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">PQC Scanner</h1>
              <p className="text-xs text-slate-400">Security Dashboard</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.path

            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                  isActive
                    ? 'bg-gradient-to-r from-indigo-500/20 to-purple-600/20 text-white border border-indigo-500/30'
                    : 'text-slate-400 hover:bg-white/5 hover:text-white'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </Link>
            )
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-white/10">
          <p className="text-xs text-slate-500 text-center">
            AI-PQC Scanner v1.0
          </p>
        </div>
      </div>
    </div>
  )
}
