/**
 * 환경 설정 관리 유틸리티
 *
 * Vite의 import.meta.env를 사용하여 환경 변수 로드
 * 타입 안전성을 위해 명시적으로 환경 변수 접근
 */

interface AppConfig {
  apiBaseURL: string
  isDevelopment: boolean
  isProduction: boolean
}

/**
 * 환경 변수 검증 및 기본값 설정
 */
const getEnvVar = (key: string, defaultValue?: string): string => {
  const value = import.meta.env[key]
  if (value === undefined || value === '') {
    if (defaultValue === undefined) {
      console.warn(`환경 변수 ${key}가 설정되지 않았습니다.`)
    }
    return defaultValue ?? ''
  }
  return value
}

/**
 * 애플리케이션 설정 객체
 */
export const config: AppConfig = {
  apiBaseURL: getEnvVar('VITE_API_BASE_URL', 'http://localhost:3000'),
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
}

/**
 * 개발 환경에서 설정 값 출력 (디버깅용)
 */
if (config.isDevelopment) {
  console.info('App Config:', config)
}
