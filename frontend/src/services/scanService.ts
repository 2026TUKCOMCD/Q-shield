import { logInfo, logError } from '../utils/logger'

/**
 * 스캔 상태 타입
 */
export type ScanStatus = 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED'

/**
 * 스캔 시작 요청 타입
 */
export interface InitiateScanRequest {
  githubUrl: string
}

/**
 * 스캔 시작 응답 타입
 */
export interface InitiateScanResponse {
  uuid: string
}

/**
 * 스캔 상태 응답 타입
 */
export interface ScanStatusResponse {
  uuid: string
  status: ScanStatus
  progress: number
}

/**
 * 스캔 히스토리 아이템 타입
 */
export interface ScanHistoryItem {
  uuid: string
  githubUrl: string
  status: ScanStatus
  progress: number
  createdAt: string
  updatedAt: string
}

/**
 * UUID 생성 헬퍼
 */
const generateUUID = (): string => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

/**
 * 로컬 스토리지에서 스캔 목록 로드
 */
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

/**
 * 로컬 스토리지에 스캔 목록 저장
 */
const saveScansToStorage = (scans: ScanHistoryItem[]): void => {
  try {
    localStorage.setItem('pqc-scanner-scans', JSON.stringify(scans))
  } catch (error) {
    logError('Failed to save scans to storage', error)
  }
}

/**
 * 스캔 서비스 (localStorage 기반 Mock 구현)
 * 백엔드 API 연동 전까지 완전히 동작하는 mock 구현
 */
export const scanService = {
  /**
   * 새로운 스캔 시작
   * Mock: 즉시 UUID를 반환하고 로컬 스토리지에 저장
   */
  async initiateScan(githubUrl: string): Promise<InitiateScanResponse> {
    logInfo('Initiating scan', { githubUrl })

    // 시뮬레이션을 위한 약간의 지연
    await new Promise((resolve) => setTimeout(resolve, 500))

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

    // 기존 스캔 목록에 추가
    const existingScans = loadScansFromStorage()
    existingScans.unshift(newScan) // 최신순으로 앞에 추가
    saveScansToStorage(existingScans)

    // 비동기로 상태 업데이트 시뮬레이션
    setTimeout(() => {
      const scans = loadScansFromStorage()
      const scanIndex = scans.findIndex((s) => s.uuid === uuid)
      if (scanIndex >= 0) {
        scans[scanIndex].status = 'IN_PROGRESS'
        scans[scanIndex].progress = 10
        scans[scanIndex].updatedAt = new Date().toISOString()
        saveScansToStorage(scans)

        // 진행률 업데이트 시뮬레이션
        const progressInterval = setInterval(() => {
          const currentScans = loadScansFromStorage()
          const currentScanIndex = currentScans.findIndex((s) => s.uuid === uuid)
          if (currentScanIndex >= 0) {
            const currentScan = currentScans[currentScanIndex]
            if (currentScan.progress < 90) {
              currentScan.progress += 10
              currentScan.updatedAt = new Date().toISOString()
              saveScansToStorage(currentScans)
            } else {
              // 완료 처리
              currentScan.status = 'COMPLETED'
              currentScan.progress = 100
              currentScan.updatedAt = new Date().toISOString()
              saveScansToStorage(currentScans)
              clearInterval(progressInterval)
            }
          } else {
            clearInterval(progressInterval)
          }
        }, 2000)
      }
    }, 1000)

    return { uuid }
  },

  /**
   * 스캔 상태 조회
   * Mock: 로컬 스토리지에서 조회
   */
  async getScanStatus(uuid: string): Promise<ScanStatusResponse> {
    const scans = loadScansFromStorage()
    const scan = scans.find((s) => s.uuid === uuid)

    if (!scan) {
      throw new Error(`Scan with UUID ${uuid} not found`)
    }

    return {
      uuid: scan.uuid,
      status: scan.status,
      progress: scan.progress,
    }
  },

  /**
   * 모든 스캔 히스토리 조회
   * Mock: 로컬 스토리지에서 모든 스캔 반환
   */
  async getAllScans(): Promise<ScanHistoryItem[]> {
    return loadScansFromStorage()
  },
}
