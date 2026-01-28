import { Routes, Route, Navigate } from 'react-router-dom'
import { Sidebar } from './components/Sidebar'
import { ScanInput } from './pages/ScanInput'
import { ScanHistory } from './pages/ScanHistory'

function App() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Navigate to="/scans/new" replace />} />
          <Route path="/scans/new" element={<ScanInput />} />
          <Route path="/scans/history" element={<ScanHistory />} />
          <Route path="*" element={<Navigate to="/scans/new" replace />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
