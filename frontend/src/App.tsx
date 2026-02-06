import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { Sidebar } from './components/Sidebar'
import { MobileNav } from './components/MobileNav'
import { ScanInput } from './pages/ScanInput'
import { ScanHistory } from './pages/ScanHistory'
import { Dashboard } from './pages/Dashboard'
import { Recommendations } from './pages/Recommendations'
import { RepositoryHeatmap } from './pages/RepositoryHeatmap'
import { InventoryDetail } from './pages/InventoryDetail'
import { AuthPage } from './pages/AuthPage'
import { useAuth } from './auth/AuthContext'

function App() {
  const location = useLocation()
  const { isAuthenticated, isLoading } = useAuth()
  const isAuthRoute = location.pathname.startsWith('/auth')

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#020617] text-white flex items-center justify-center">
        Loading...
      </div>
    )
  }

  return (
    <div className="flex min-h-screen">
      {!isAuthRoute && isAuthenticated && <Sidebar />}
      {!isAuthRoute && isAuthenticated && <MobileNav />}
      <main className="flex-1">
        <Routes>
          <Route
            path="/"
            element={<Navigate to={isAuthenticated ? '/scans/new' : '/auth/login'} replace />}
          />
          <Route
            path="/auth/login"
            element={isAuthenticated ? <Navigate to="/scans/new" replace /> : <AuthPage />}
          />
          <Route
            path="/auth/signup"
            element={isAuthenticated ? <Navigate to="/scans/new" replace /> : <AuthPage />}
          />
          <Route
            path="/scans/new"
            element={isAuthenticated ? <ScanInput /> : <Navigate to="/auth/login" replace />}
          />
          <Route
            path="/scans/history"
            element={isAuthenticated ? <ScanHistory /> : <Navigate to="/auth/login" replace />}
          />
          <Route
            path="/dashboard/:uuid"
            element={isAuthenticated ? <Dashboard /> : <Navigate to="/auth/login" replace />}
          />
          <Route
            path="/scans/:uuid/recommendations"
            element={isAuthenticated ? <Recommendations /> : <Navigate to="/auth/login" replace />}
          />
          <Route
            path="/scans/:uuid/heatmap"
            element={isAuthenticated ? <RepositoryHeatmap /> : <Navigate to="/auth/login" replace />}
          />
          <Route
            path="/scans/:uuid/inventory/:assetId"
            element={isAuthenticated ? <InventoryDetail /> : <Navigate to="/auth/login" replace />}
          />
          <Route
            path="*"
            element={<Navigate to={isAuthenticated ? '/scans/new' : '/auth/login'} replace />}
          />
        </Routes>
      </main>
    </div>
  )
}

export default App
