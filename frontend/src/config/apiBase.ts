/**
 * 后端 API 根地址。
 * 开发环境默认空字符串，配合 Vite proxy 走同源 `/api`，避免 CORS。
 * 生产可设置 VITE_API_BASE_URL，例如 https://api.example.com
 */
export function getApiBaseUrl(): string {
  const raw = import.meta.env.VITE_API_BASE_URL as string | undefined
  if (raw !== undefined && raw !== '') {
    return raw.replace(/\/+$/, '')
  }
  if (import.meta.env.DEV) {
    return ''
  }
  return 'http://localhost:8000'
}
