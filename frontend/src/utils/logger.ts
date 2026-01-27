/**
 * 로깅 유틸리티
 *
 * 개발/프로덕션 환경에 따라 적절한 로깅 레벨 제공
 * - 개발: console.log/error/warn 등 상세 로깅
 * - 프로덕션: 에러만 로깅 (선택적으로 외부 서비스로 전송 가능)
 */

export enum LogLevel {
  DEBUG = 'DEBUG',
  INFO = 'INFO',
  WARN = 'WARN',
  ERROR = 'ERROR',
}

interface LogContext {
  [key: string]: unknown
}

const isDevelopment = import.meta.env.DEV

/**
 * 로그 레벨에 따른 출력 여부 결정
 */
const shouldLog = (level: LogLevel): boolean => {
  if (isDevelopment) {
    return true // 개발 환경에서는 모든 로그 출력
  }
  // 프로덕션에서는 WARN, ERROR만 출력
  return level === LogLevel.WARN || level === LogLevel.ERROR
}

/**
 * 로그 포맷팅
 */
const formatLog = (level: LogLevel, message: string, context?: LogContext): string => {
  const timestamp = new Date().toISOString()
  const contextStr = context ? ` | Context: ${JSON.stringify(context)}` : ''
  return `[${timestamp}] [${level}] ${message}${contextStr}`
}

/**
 * Debug 레벨 로깅
 */
export const logDebug = (message: string, context?: LogContext): void => {
  if (shouldLog(LogLevel.DEBUG)) {
    console.debug(formatLog(LogLevel.DEBUG, message, context))
  }
}

/**
 * Info 레벨 로깅
 */
export const logInfo = (message: string, context?: LogContext): void => {
  if (shouldLog(LogLevel.INFO)) {
    console.info(formatLog(LogLevel.INFO, message, context))
  }
}

/**
 * Warn 레벨 로깅
 */
export const logWarn = (message: string, context?: LogContext): void => {
  if (shouldLog(LogLevel.WARN)) {
    console.warn(formatLog(LogLevel.WARN, message, context))
  }
}

/**
 * Error 레벨 로깅
 */
export const logError = (message: string, error?: Error | unknown, context?: LogContext): void => {
  if (shouldLog(LogLevel.ERROR)) {
    const errorContext = {
      ...context,
      error: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined,
    }
    console.error(formatLog(LogLevel.ERROR, message, errorContext))
  }
}
