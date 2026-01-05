/**
 * Mapbox API 服务
 */
import { MAPBOX_CONFIG, API_CONFIG } from '@/config'
import type { GeocodeFeature } from '@/types/api'

/**
 * 地理编码搜索
 */
export const geocodingApi = {
  /**
   * 搜索地点
   */
  search: async (
    query: string,
    limit = API_CONFIG.SEARCH_RESULT_LIMIT
  ): Promise<GeocodeFeature[]> => {
    if (!query || query.trim().length < API_CONFIG.SEARCH_MIN_LENGTH) {
      return []
    }

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT)

    try {
      const url = `${MAPBOX_CONFIG.GEOCODING_API_URL}/${encodeURIComponent(query)}.json`
      const params = new URLSearchParams({
        access_token: MAPBOX_CONFIG.ACCESS_TOKEN,
        limit: limit.toString(),
      })

      const response = await fetch(`${url}?${params.toString()}`, {
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new Error(`Geocoding API error: ${response.statusText}`)
      }

      const data = await response.json()
      return data.features || []
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.error('搜索超时')
      } else {
        console.error('搜索错误:', error)
      }
      return []
    }
  },
}
