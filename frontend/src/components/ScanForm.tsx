import { useState, type FormEvent } from 'react'
import { scanService, type InitiateScanResponse } from '../services/scanService'
import { logError } from '../utils/logger'
import { Github, Loader2, AlertCircle } from 'lucide-react'

interface ScanFormProps {
  onScanInitiated?: (response: InitiateScanResponse) => void
  onError?: (message: string) => void
  onUrlChange?: (url: string) => void
}

/**
 * GitHub URL 입력 폼 컴포넌트
 * T008: Modern Cyber-security Dashboard 스타일 적용
 */
export const ScanForm = ({ onScanInitiated, onError, onUrlChange }: ScanFormProps) => {
  const [githubUrl, setGithubUrl] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isFocused, setIsFocused] = useState(false)
  const [localError, setLocalError] = useState<string | null>(null)

  /**
   * GitHub URL 유효성 검사
   */
  const isValidGitHubUrl = (url: string): boolean => {
    try {
      const urlObj = new URL(url)
      return (
        (urlObj.hostname === 'github.com' || urlObj.hostname === 'www.github.com') &&
        urlObj.pathname.split('/').filter(Boolean).length >= 2
      )
    } catch {
      return false
    }
  }

  /**
   * 폼 제출 핸들러
   */
  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setLocalError(null)

    // URL 유효성 검사
    if (!githubUrl.trim()) {
      const errorMsg = 'GitHub URL을 입력해주세요.'
      setLocalError(errorMsg)
      onError?.(errorMsg)
      return
    }

    if (!isValidGitHubUrl(githubUrl)) {
      const errorMsg = '올바른 GitHub URL이 아닙니다. GitHub 저장소 URL을 입력해주세요. (예: https://github.com/owner/repo)'
      setLocalError(errorMsg)
      onError?.(errorMsg)
      return
    }

    setIsSubmitting(true)

    try {
      const response = await scanService.initiateScan(githubUrl.trim())
      setGithubUrl('') // 성공 시 입력 필드 초기화
      setLocalError(null)
      onScanInitiated?.(response)
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : '스캔 시작에 실패했습니다.'
      logError('Failed to initiate scan', error)
      setLocalError(errorMessage)
      onError?.(errorMessage)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-6">
      {/* Error Message */}
      {localError && (
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-3 text-red-400 animate-in fade-in duration-200">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <p className="text-sm">{localError}</p>
        </div>
      )}

      {/* Input Field */}
      <div className="relative">
        <label htmlFor="github-url" className="block text-sm font-medium mb-2 text-slate-300">
          GitHub Repository URL
        </label>
        <div className="relative">
          {/* Neon Glow Effect on Focus */}
          {isFocused && (
            <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-500 rounded-lg blur opacity-50 animate-pulse" />
          )}
          
          <div className="relative flex items-center">
            <div className="absolute left-4 flex items-center pointer-events-none">
              <Github className="w-5 h-5 text-slate-400" />
            </div>
            <input
              id="github-url"
              type="url"
              value={githubUrl}
              onChange={(e) => {
                setGithubUrl(e.target.value)
                onUrlChange?.(e.target.value)
                setLocalError(null)
              }}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder="https://github.com/owner/repository"
              disabled={isSubmitting}
              className="w-full pl-12 pr-4 py-4 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:bg-white/10 focus:border-indigo-500/50 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed backdrop-blur-sm"
            />
          </div>
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isSubmitting || !githubUrl.trim()}
        className="w-full py-4 px-6 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl hover:shadow-purple-500/25 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {isSubmitting ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>Scanning...</span>
          </>
        ) : (
          <span>Start Scan</span>
        )}
      </button>
    </form>
  )
}
