import axios, {
  type AxiosInstance,
  type InternalAxiosRequestConfig,
  type AxiosResponse,
} from 'axios'
import { config } from '../config'
import { tokenStore } from '../auth/tokenStore'
import { handleError } from '../utils/errorHandler'
import { logDebug, logError, logInfo } from '../utils/logger'

const apiClient: AxiosInstance = axios.create({
  baseURL: config.apiBaseURL,
  timeout: 30_000,
  withCredentials: false,
})

apiClient.interceptors.request.use(
  (requestConfig: InternalAxiosRequestConfig): InternalAxiosRequestConfig => {
    const accessToken = tokenStore.getAccessToken()
    if (accessToken) {
      requestConfig.headers.set('Authorization', `Bearer ${accessToken}`)
    }

    logDebug('API Request', {
      method: requestConfig.method?.toUpperCase(),
      url: requestConfig.url,
      baseURL: requestConfig.baseURL,
      auth: accessToken ? 'bearer' : 'none',
    })

    return requestConfig
  },
  (error) => {
    logError('API Request Error', error)
    return Promise.reject(handleError(error))
  },
)

apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    logInfo('API Response', {
      status: response.status,
      url: response.config.url,
      method: response.config.method,
    })

    return response
  },
  (error) => {
    if (error?.response?.status === 401) {
      tokenStore.clear()
      window.dispatchEvent(new Event('auth:unauthorized'))
    }
    const appError = handleError(error)
    return Promise.reject(appError)
  },
)

export { apiClient }
