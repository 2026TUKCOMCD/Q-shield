import { type AxiosError } from 'axios'
import { logError, logWarn } from './logger'

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

export const handleAxiosError = (error: AxiosError): AppError => {
  if (error.response) {
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
  }

  if (error.request) {
    logError('Network Error', error, {
      url: error.config?.url,
      method: error.config?.method,
    })

    return {
      type: ErrorType.NETWORK_ERROR,
      message: 'Network error occurred. Please check your connection.',
      originalError: error,
    }
  }

  logError('Request Setup Error', error)
  return {
    type: ErrorType.UNKNOWN_ERROR,
    message: error.message || 'An unknown error occurred.',
    originalError: error,
  }
}

export const handleGenericError = (error: unknown): AppError => {
  if (error instanceof Error) {
    logError('Generic Error', error)
    return {
      type: ErrorType.UNKNOWN_ERROR,
      message: error.message || 'An unknown error occurred.',
      originalError: error,
    }
  }

  logWarn('Unknown Error Type', { error })
  return {
    type: ErrorType.UNKNOWN_ERROR,
    message: 'An unknown error occurred.',
    originalError: error,
  }
}

export const handleError = (error: unknown): AppError => {
  const axiosError = error as AxiosError
  if (axiosError.isAxiosError) {
    return handleAxiosError(axiosError)
  }

  return handleGenericError(error)
}

export const getUserFriendlyMessage = (error: AppError): string => {
  switch (error.type) {
    case ErrorType.NETWORK_ERROR:
      return 'Please check your network connection.'
    case ErrorType.API_ERROR:
      if (error.statusCode === 404) {
        return 'Requested resource was not found.'
      }
      if (error.statusCode === 401) {
        return 'Authentication is required. Please sign in again.'
      }
      if (error.statusCode === 403) {
        return 'You do not have permission to access this resource.'
      }
      if (error.statusCode && error.statusCode >= 500) {
        return 'Server error occurred. Please try again later.'
      }
      return error.message
    case ErrorType.VALIDATION_ERROR:
      return error.message
    default:
      return 'An error occurred. Please try again later.'
  }
}
