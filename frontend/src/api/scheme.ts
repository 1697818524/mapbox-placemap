/**
 * 样式方案生成 API 服务
 */
import { API_CONFIG } from '@/config'
import type { ColorScheme } from '@/stores'

/**
 * 带 ID 的颜色方案
 */
export interface ColorSchemeWithId extends ColorScheme {
  /** 方案唯一标识 */
  id: string
}

/**
 * 生成方案请求参数
 */
export interface GenerateSchemesRequest {
  /** 当前颜色方案 */
  currentScheme: ColorScheme
  /** 生成方案数量 */
  count: number
}

/**
 * 生成方案响应
 */
export interface GenerateSchemesResponse {
  /** 生成的方案列表（包含 id） */
  schemes: ColorSchemeWithId[]
}

/**
 * 样式方案生成服务
 */
export const schemeApi = {
  /**
   * 生成多个修改后的样式方案
   * @param request 生成请求参数
   * @returns 生成的方案列表（包含 id）
   */
  generateSchemes: async (
    request: GenerateSchemesRequest
  ): Promise<GenerateSchemesResponse> => {
    const { currentScheme, count } = request

    try {
      // TODO: 替换为实际的后端 API 地址
      const backendUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
      const url = `${backendUrl}/api/schemes/generate`

      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT * 3)

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          currentScheme,
          count,
        }),
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new Error(`生成方案失败: ${response.statusText}`)
      }

      const data: GenerateSchemesResponse = await response.json()
      return data
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.error('生成方案超时')
        throw new Error('生成方案超时，请稍后重试')
      } else {
        console.error('生成方案错误:', error)
        throw error
      }
    }
  },
}
