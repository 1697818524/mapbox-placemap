/**
 * 图片搜索 API 服务
 */
import type { ImageResult } from '@/types/api'

/**
 * 图片搜索服务
 * 注意：由于跨域限制，实际使用时需要通过后端代理
 */
export const imageApi = {
  /**
   * 搜索图片（模拟实现）
   * 实际项目中应该通过后端API代理
   * @param keyword 搜索关键词
   * @param count 返回图片数量
   * @param imageLabel 图片标签（用于国际化）
   */
  search: async (keyword: string, count = 9, imageLabel = '图片'): Promise<ImageResult[]> => {
    try {
      // 这里使用模拟数据
      // 实际使用时，你需要：
      // 1. 通过后端API代理图片搜索服务
      // 2. 或者使用其他图片搜索API（如 Unsplash API、Pixabay API 等）

      const mockImages: ImageResult[] = []

      for (let i = 0; i < count; i++) {
        mockImages.push({
          url: `https://picsum.photos/400/300?random=${i}&keyword=${encodeURIComponent(keyword)}`,
          thumbnail: `https://picsum.photos/200/150?random=${i}&keyword=${encodeURIComponent(keyword)}`,
          title: `${keyword} - ${imageLabel} ${i + 1}`,
          width: 400,
          height: 300,
        })
      }

      // 模拟网络延迟
      await new Promise(resolve => setTimeout(resolve, 1000))

      return mockImages
    } catch (error) {
      console.error('搜索图片失败:', error)
      return []
    }
  },
}
