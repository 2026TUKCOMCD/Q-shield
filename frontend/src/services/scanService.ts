import { apiClient } from '../api'
import { config } from '../config'
import { handleError, type AppError, ErrorType } from '../utils/errorHandler'
import { logInfo, logError } from '../utils/logger'

export type ScanStatus = 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED'

export interface InitiateScanRequest {
  githubUrl: string
}

export interface InitiateScanResponse {
  uuid: string
}

export interface ScanStatusResponse {
  uuid: string
  status: ScanStatus
  progress: number
}

export interface ScanHistoryItem {
  uuid: string
  githubUrl: string
  status: ScanStatus
  progress: number
  createdAt: string
  updatedAt: string
}

const isAppError = (error: unknown): error is AppError => {
  return typeof error === 'object' && error !== null && 'type' in error && 'message' in error
}

const toAppError = (error: unknown): AppError => {
  return isAppError(error) ? error : (handleError(error) as AppError)
}

const shouldUseDevFallback = (error: AppError): boolean => {
  if (!config.isDevelopment) {
    return false
  }
  if (error.type === ErrorType.NETWORK_ERROR) {
    return true
  }
  return error.type === ErrorType.API_ERROR && (error.statusCode ?? 0) >= 500
}

const generateUUID = (): string => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

const loadScansFromStorage = (): ScanHistoryItem[] => {
  try {
    const stored = localStorage.getItem('pqc-scanner-scans')
    if (stored) {
      return JSON.parse(stored) as ScanHistoryItem[]
    }
  } catch (error) {
    logError('Failed to load scans from storage', error)
  }
  return []
}

const saveScansToStorage = (scans: ScanHistoryItem[]): void => {
  try {
    localStorage.setItem('pqc-scanner-scans', JSON.stringify(scans))
  } catch (error) {
    logError('Failed to save scans to storage', error)
  }
}

const fallbackInitiateScan = async (githubUrl: string): Promise<InitiateScanResponse> => {
  const uuid = generateUUID()
  const now = new Date().toISOString()

  const newScan: ScanHistoryItem = {
    uuid,
    githubUrl,
    status: 'PENDING',
    progress: 0,
    createdAt: now,
    updatedAt: now,
  }

  const existingScans = loadScansFromStorage()
  existingScans.unshift(newScan)
  saveScansToStorage(existingScans)

  return { uuid }
}

const fallbackGetScanStatus = async (uuid: string): Promise<ScanStatusResponse> => {
  const scans = loadScansFromStorage()
  const scanIndex = scans.findIndex((s) => s.uuid === uuid)

  if (scanIndex === -1) {
    throw new Error(`Scan with UUID ${uuid} not found`)
  }

  const scan = scans[scanIndex]

  if (scan.status === 'PENDING' || scan.status === 'IN_PROGRESS') {
    const increment = 25 + Math.random() * 10
    const newProgress = Math.min(100, scan.progress + increment)

    if (scan.status === 'PENDING' && newProgress > 0) {
      scan.status = 'IN_PROGRESS'
    }

    scan.progress = Math.round(newProgress)
    scan.updatedAt = new Date().toISOString()

    if (scan.progress >= 100) {
      scan.status = 'COMPLETED'
      scan.progress = 100
    }

    saveScansToStorage(scans)
  }

  return {
    uuid: scan.uuid,
    status: scan.status,
    progress: scan.progress,
  }
}

export const scanService = {
  async initiateScan(githubUrl: string): Promise<InitiateScanResponse> {
    logInfo('Initiating scan', { githubUrl })

    try {
      const response = await apiClient.post<InitiateScanResponse>('/scans', { githubUrl })
      return response.data
    } catch (error) {
      const appError = toAppError(error)
      logError('Failed to initiate scan', appError)

      if (shouldUseDevFallback(appError)) {
        return fallbackInitiateScan(githubUrl)
      }

      throw appError
    }
  },

  async getScanStatus(uuid: string): Promise<ScanStatusResponse> {
    try {
      const response = await apiClient.get<ScanStatusResponse>(`/scans/${uuid}/status`)
      return response.data
    } catch (error) {
      const appError = toAppError(error)
      logError('Failed to get scan status', appError)

      if (shouldUseDevFallback(appError)) {
        return fallbackGetScanStatus(uuid)
      }

      throw appError
    }
  },

  async getAllScans(query?: string): Promise<ScanHistoryItem[]> {
    try {
      const response = await apiClient.get<ScanHistoryItem[]>('/scans', {
        params: query ? { query } : undefined,
      })
      return response.data
    } catch (error) {
      const appError = toAppError(error)
      logError('Failed to get all scans', appError)

      if (shouldUseDevFallback(appError)) {
        const scans = loadScansFromStorage()
        if (!query || !query.trim()) {
          return scans
        }
        const term = query.toLowerCase()
        return scans.filter((scan) => scan.githubUrl.toLowerCase().includes(term))
      }

      throw appError
    }
  },

  async deleteScan(uuid: string): Promise<void> {
    try {
      await apiClient.delete(`/scans/${uuid}`)
    } catch (error) {
      const appError = toAppError(error)
      logError('Failed to delete scan', appError)

      if (shouldUseDevFallback(appError)) {
        const scans = loadScansFromStorage()
        const next = scans.filter((scan) => scan.uuid !== uuid)
        saveScansToStorage(next)
        return
      }

      throw appError
    }
  },
}
