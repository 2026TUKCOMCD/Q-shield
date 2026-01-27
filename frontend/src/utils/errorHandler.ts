import { type AxiosError } from 'axios'
import { logError, logWarn } from './logger'

/**
 * 에러 타입 정의
 */
export enum ErrorType {
  NETWORK_ERROR = 'NETWORK_ERROR',
  API_ERROR = 'API_ERROR',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  UNKNOWN_ERROR = 'UNKNOWN_ERROR',
}

export interface AppError {
  type: ErrorType
  message: string
  statusCode?: number
  originalError?: unknown
}

/**
 * Axios 에러를 AppError로 변환
 */
export const handleAxiosError = (error: AxiosError): AppError => {
  if (error.response) {
    // 서버가 응답했지만 에러 상태 코드
    const statusCode = error.response.status
    const message =
      (error.response.data as { message?: string })?.message ||
      error.message ||
      `API Error: ${statusCode}`

    logError('API Error', error, {
      statusCode,
      url: error.config?.url,
      method: error.config?.method,
    })

    return {
      type: ErrorType.API_ERROR,
      message,
      statusCode,
      originalError: error,
    }
  } else if (error.request) {
    // 요청은 보냈지만 응답을 받지 못함
    logError('Network Error', error, {
      url: error.config?.url,
      method: error.config?.method,
    })

    return {
      type: ErrorType.NETWORK_ERROR,
      message: '네트워크 오류가 발생했습니다. 연결을 확인해주세요.',
      originalError: error,
    }
  } else {
    // 요청 설정 중 에러 발생
    logError('Request Setup Error', error)

    return {
      type: ErrorType.UNKNOWN_ERROR,
      message: error.message || '알 수 없는 오류가 발생했습니다.',
      originalError: error,
    }
  }
}

/**
 * 일반 에러를 AppError로 변환
 */
export const handleGenericError = (error: unknown): AppError => {
  if (error instanceof Error) {
    logError('Generic Error', error)

    return {
      type: ErrorType.UNKNOWN_ERROR,
      message: error.message || '알 수 없는 오류가 발생했습니다.',
      originalError: error,
    }
  }

  logWarn('Unknown Error Type', { error })

  return {
    type: ErrorType.UNKNOWN_ERROR,
    message: '알 수 없는 오류가 발생했습니다.',
    originalError: error,
  }
}

/**
 * 에러 핸들러 (통합)
 * Axios 에러인지 일반 에러인지 자동 판단하여 처리
 */
export const handleError = (error: unknown): AppError => {
  // Axios 에러인지 확인
  const axiosError = error as AxiosError
  if (axiosError.isAxiosError) {
    return handleAxiosError(axiosError)
  }

  return handleGenericError(error)
}

/**
 * 사용자 친화적인 에러 메시지 반환
 */
export const getUserFriendlyMessage = (error: AppError): string => {
  switch (error.type) {
    case ErrorType.NETWORK_ERROR:
      return '네트워크 연결을 확인해주세요.'
    case ErrorType.API_ERROR:
      if (error.statusCode === 404) {
        return '요청한 리소스를 찾을 수 없습니다.'
      }
      if (error.statusCode === 401) {
        return '인증이 필요합니다. 다시 로그인해주세요.'
      }
      if (error.statusCode === 403) {
        return '접근 권한이 없습니다.'
      }
      if (error.statusCode && error.statusCode >= 500) {
        return '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
      }
      return error.message
    case ErrorType.VALIDATION_ERROR:
      return error.message
    default:
      return '오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
  }
}
