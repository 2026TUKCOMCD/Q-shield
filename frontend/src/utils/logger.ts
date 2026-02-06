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

const shouldLog = (level: LogLevel): boolean => {
  if (isDevelopment) {
    return true
  }

  return level === LogLevel.WARN || level === LogLevel.ERROR
}

const formatLog = (level: LogLevel, message: string, context?: LogContext): string => {
  const timestamp = new Date().toISOString()
  const contextStr = context ? ` | Context: ${JSON.stringify(context)}` : ''
  return `[${timestamp}] [${level}] ${message}${contextStr}`
}

export const logDebug = (message: string, context?: LogContext): void => {
  if (shouldLog(LogLevel.DEBUG)) {
    console.debug(formatLog(LogLevel.DEBUG, message, context))
  }
}

export const logInfo = (message: string, context?: LogContext): void => {
  if (shouldLog(LogLevel.INFO)) {
    console.info(formatLog(LogLevel.INFO, message, context))
  }
}

export const logWarn = (message: string, context?: LogContext): void => {
  if (shouldLog(LogLevel.WARN)) {
    console.warn(formatLog(LogLevel.WARN, message, context))
  }
}

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
