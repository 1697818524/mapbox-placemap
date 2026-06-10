/**
 * 样式方案生成 API 服务
 */
import { API_CONFIG, getApiBaseUrl } from '@/config'
import type { ColorScheme, ColorSchemeWithId } from '@/stores'

export type { ColorSchemeWithId }

/**
 * 生成方案请求参数
 */
export interface GenerateSchemesRequest {
  /** 当前颜色方案 */
  currentScheme: ColorScheme
  /** 生成方案数量 */
  count: number
  /** 若存在，后端优先用该任务的聚类调色板生成方案 */
  jobId?: string | null
  population?: number
  generations?: number
  semanticMode?: 'local' | 'global'
  layerSemantics?: Record<string, string>
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
    const { currentScheme, count, jobId, population, generations, semanticMode, layerSemantics } = request

    try {
      const url = `${getApiBaseUrl()}/api/schemes/generate`

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
          ...(jobId ? { job_id: jobId } : {}),
          ...(population ? { population } : {}),
          ...(generations ? { generations } : {}),
          ...(semanticMode ? { semantic_mode: semanticMode } : {}),
          ...(layerSemantics ? { layer_semantics: layerSemantics } : {}),
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
