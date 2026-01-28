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
 * 네트워크 지연 시뮬레이션 (0.5-1초)
 */
const simulateNetworkDelay = (): Promise<void> => {
  const delay = 500 + Math.random() * 500 // 0.5-1초
  return new Promise((resolve) => setTimeout(resolve, delay))
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

    // 네트워크 지연 시뮬레이션
    await simulateNetworkDelay()

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

    return { uuid }
  },

  /**
   * 스캔 상태 조회
   * Mock: 폴링 시뮬레이션 - 호출될 때마다 progress를 점진적으로 증가
   */
  async getScanStatus(uuid: string): Promise<ScanStatusResponse> {
    // 네트워크 지연 시뮬레이션
    await simulateNetworkDelay()

    const scans = loadScansFromStorage()
    const scanIndex = scans.findIndex((s) => s.uuid === uuid)

    if (scanIndex === -1) {
      throw new Error(`Scan with UUID ${uuid} not found`)
    }

    const scan = scans[scanIndex]

    // 폴링 시뮬레이션: progress를 점진적으로 증가 (데모용 빠른 속도)
    if (scan.status === 'PENDING' || scan.status === 'IN_PROGRESS') {
      // 진행률 증가 (25-35%씩 랜덤하게 - 데모용 빠른 속도)
      const increment = 25 + Math.random() * 10
      const newProgress = Math.min(100, scan.progress + increment)

      // 상태 업데이트
      if (scan.status === 'PENDING' && newProgress > 0) {
        scan.status = 'IN_PROGRESS'
      }

      scan.progress = Math.round(newProgress)
      scan.updatedAt = new Date().toISOString()

      // 100%가 되면 COMPLETED로 변경
      if (scan.progress >= 100) {
        scan.status = 'COMPLETED'
        scan.progress = 100
      }

      // localStorage에 저장
      saveScansToStorage(scans)
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
    // 네트워크 지연 시뮬레이션
    await simulateNetworkDelay()
    return loadScansFromStorage()
  },
}
