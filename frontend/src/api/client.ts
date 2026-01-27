import axios, {
  type AxiosInstance,
  type InternalAxiosRequestConfig,
  type AxiosResponse,
} from 'axios'
import { config } from '../config'
import { handleError } from '../utils/errorHandler'
import { logDebug, logError, logInfo } from '../utils/logger'

/**
 * API 클라이언트 인스턴스
 *
 * - baseURL, timeout 등 공통 설정
 * - request/response 인터셉터를 통해 미들웨어 역할 수행
 * - logger와 errorHandler를 통합하여 로깅 및 에러 처리
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: config.apiBaseURL,
  timeout: 30_000,
  withCredentials: false,
})

// Request interceptor (middleware-like)
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig): InternalAxiosRequestConfig => {
    // 요청 로깅
    logDebug('API Request', {
      method: config.method?.toUpperCase(),
      url: config.url,
      baseURL: config.baseURL,
    })

    // TODO: 인증 토큰 등 공통 헤더 추가 필요 시 여기에 구현
    // if (authToken) {
    //   config.headers = config.headers || {}
    //   config.headers.Authorization = `Bearer ${authToken}`
    // }

    return config
  },
  (error) => {
    // 요청 에러 로깅 및 공통 처리
    logError('API Request Error', error)
    return Promise.reject(handleError(error))
  },
)

// Response interceptor (middleware-like)
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // 응답 로깅
    logInfo('API Response', {
      status: response.status,
      url: response.config.url,
      method: response.config.method,
    })

    return response
  },
  (error) => {
    // 글로벌 에러 핸들러로 위임
    const appError = handleError(error)
    return Promise.reject(appError)
  },
)

export { apiClient }
