/**
 * 图片搜索 API 服务
 */
import { API_CONFIG, getApiBaseUrl } from '@/config'
import type { ImageResult } from '@/types/api'

const backendUrl = () => getApiBaseUrl()

export interface ImageCollectRequest {
  location: string
  urls: string[]
}

export interface CollectedImageItem {
  image_id: string
  filename: string
  path: string
  source: string
  original_url?: string | null
}

export interface ImageCollectResponse {
  location: string
  image_ids: string[]
  items: CollectedImageItem[]
}

async function readFetchError(res: Response): Promise<string> {
  try {
    const j = await res.json()
    if (j?.detail?.message) return j.detail.message
    if (typeof j?.detail === 'string') return j.detail
  } catch {
    /* ignore */
  }
  return res.statusText
}

/**
 * 列表/大图展示用：走同源 `/api/images/proxy`，避免百度等图床在浏览器里拦 Referer。
 * 构建样本集时的 collect 请求请仍使用接口返回的原始 `url`。
 */
export function getImageProxyUrl(remoteUrl: string): string {
  const u = remoteUrl?.trim()
  if (!u || !/^https?:\/\//i.test(u)) {
    return u || ''
  }
  return `${backendUrl()}/api/images/proxy?url=${encodeURIComponent(u)}`
}

/**
 * 图片搜索服务
 */
export const imageApi = {
  /**
   * 搜索图片
   * @param keyword 搜索关键词
   * @param count 返回图片数量
   * @param _imageLabel 图片标签（已废弃，保留以兼容旧代码）
   */
  search: async (keyword: string, count = 9, _imageLabel = '图片'): Promise<ImageResult[]> => {
    if (!keyword || keyword.trim().length === 0) {
      return []
    }

    try {
      // 后端API地址
      const url = `${backendUrl()}/api/images/search`

      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT)

      const params = new URLSearchParams({
        keyword: keyword.trim(),
        count: count.toString(),
      })

      const response = await fetch(`${url}?${params.toString()}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new Error(`图片搜索失败: ${response.statusText}`)
      }

      const data: ImageResult[] = await response.json()
      return data
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.error('搜索图片超时')
      } else {
        console.error('搜索图片失败:', error)
      }
      return []
    }
  },

  /**
   * 将图片 URL 下载到后端 data/ingest/{location}/，返回 image_ids
   */
  collect: async (payload: ImageCollectRequest): Promise<ImageCollectResponse> => {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT * 3)
    const res = await fetch(`${backendUrl()}/api/images/collect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        location: payload.location,
        urls: payload.urls,
      }),
      signal: controller.signal,
    })
    clearTimeout(timeoutId)
    if (!res.ok) {
      throw new Error(await readFetchError(res))
    }
    return res.json()
  },

  /**
   * 本地上传到后端 data/ingest/{location}/，返回 image_ids（multipart，字段名 files）
   */
  upload: async (location: string, files: File[]): Promise<ImageCollectResponse> => {
    if (!files.length) {
      throw new Error('未选择文件')
    }
    const fd = new FormData()
    for (const f of files) {
      fd.append('files', f)
    }
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT * 12)
    const qs = new URLSearchParams({ location })
    const res = await fetch(`${backendUrl()}/api/images/upload?${qs.toString()}`, {
      method: 'POST',
      body: fd,
      signal: controller.signal,
    })
    clearTimeout(timeoutId)
    if (!res.ok) {
      throw new Error(await readFetchError(res))
    }
    return res.json()
  },
}
