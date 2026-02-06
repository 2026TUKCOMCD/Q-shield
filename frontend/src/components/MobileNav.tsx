import { Link, useLocation } from 'react-router-dom'
import { Scan, History, Menu, X, Shield, LogOut } from 'lucide-react'
import { useState } from 'react'
import { useAuth } from '../auth/AuthContext'

export const MobileNav = () => {
  const location = useLocation()
  const [isOpen, setIsOpen] = useState(false)
  const { user, logout } = useAuth()

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
    <>
      <div className="md:hidden fixed top-4 left-4 z-50">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="p-3 bg-slate-900/80 backdrop-blur-md border border-white/10 rounded-lg text-white hover:bg-white/10 transition-colors"
          aria-label="Toggle menu"
        >
          {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>
      {isOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 md:hidden"
            onClick={() => setIsOpen(false)}
          />
          <div className="fixed left-0 top-0 h-full w-64 bg-slate-900/95 backdrop-blur-md border-r border-white/10 z-50 md:hidden animate-in slide-in-from-left duration-300">
            <div className="flex flex-col h-full">
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
              <nav className="flex-1 p-4 space-y-2">
                {navItems.map((item) => {
                  const Icon = item.icon
                  const isActive = location.pathname === item.path

                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setIsOpen(false)}
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
              <div className="p-4 border-t border-white/10">
                <div className="mb-3 text-xs text-slate-400 truncate">{user?.email}</div>
                <button
                  onClick={() => {
                    logout()
                    setIsOpen(false)
                  }}
                  className="w-full mb-3 px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 hover:text-white flex items-center justify-center gap-2"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  )
}
