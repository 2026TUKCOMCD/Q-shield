interface AppConfig {
  apiBaseURL: string
  isDevelopment: boolean
  isProduction: boolean
}

const getEnvVar = (key: string, defaultValue?: string): string => {
  const value = import.meta.env[key]
  if (value === undefined || value === '') {
    if (defaultValue === undefined) {
      console.warn(`Missing environment variable: ${key}`)
    }
    return defaultValue ?? ''
  }
  return value
}

export const config: AppConfig = {
  apiBaseURL: getEnvVar('VITE_API_BASE_URL', 'http://localhost:8000/api'),
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
}

if (config.isDevelopment) {
  console.info('App Config:', config)
}
