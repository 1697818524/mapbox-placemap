/**
 * 验证工具函数
 */
export const validators = {
  /**
   * 验证经纬度是否有效
   */
  isLngLat(lng: number, lat: number): boolean {
    return lng >= -180 && lng <= 180 && lat >= -90 && lat <= 90
  },

  /**
   * 验证字符串是否非空
   */
  isNotEmpty(value: string): boolean {
    return value.trim().length > 0
  },

  /**
   * 验证字符串长度是否满足最小值
   */
  minLength(value: string, min: number): boolean {
    return value.trim().length >= min
  },

  /**
   * 验证搜索查询是否有效
   */
  isValidSearchQuery(query: string, minLength = 2): boolean {
    return this.isNotEmpty(query) && this.minLength(query, minLength)
  },
}
