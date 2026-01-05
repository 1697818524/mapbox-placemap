/**
 * 本地存储工具函数
 */
export const storage = {
  /**
   * 获取存储的值
   */
  get<T>(key: string, defaultValue?: T): T | null {
    try {
      const item = localStorage.getItem(key)
      return item ? JSON.parse(item) : (defaultValue ?? null)
    } catch (error) {
      console.error(`Storage get error for key "${key}":`, error)
      return defaultValue ?? null
    }
  },

  /**
   * 设置存储的值
   */
  set<T>(key: string, value: T): void {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch (error) {
      console.error(`Storage set error for key "${key}":`, error)
    }
  },

  /**
   * 移除存储的值
   */
  remove(key: string): void {
    try {
      localStorage.removeItem(key)
    } catch (error) {
      console.error(`Storage remove error for key "${key}":`, error)
    }
  },

  /**
   * 清空所有存储
   */
  clear(): void {
    try {
      localStorage.clear()
    } catch (error) {
      console.error('Storage clear error:', error)
    }
  },
}
