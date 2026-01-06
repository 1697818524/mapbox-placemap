/**
 * 图片搜索 API 服务
 */
import { API_CONFIG } from '@/config'
import type { ImageResult } from '@/types/api'

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
      const backendUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
      const url = `${backendUrl}/api/images/search`

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
}
