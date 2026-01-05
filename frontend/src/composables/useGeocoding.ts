/**
 * 地理编码搜索组合式函数
 */
import { ref } from 'vue'
import { geocodingApi } from '@/api'
import { validators } from '@/utils'
import { API_CONFIG } from '@/config'
import type { GeocodeFeature } from '@/types/api'

export function useGeocoding() {
  const searchQuery = ref('')
  const searchResults = ref<GeocodeFeature[]>([])
  const selectedLocation = ref<GeocodeFeature | null>(null)
  const isSearching = ref(false)

  /**
   * 执行搜索
   */
  const doSearch = async () => {
    if (!validators.isValidSearchQuery(searchQuery.value, API_CONFIG.SEARCH_MIN_LENGTH)) {
      searchResults.value = []
      return
    }

    isSearching.value = true
    try {
      const results = await geocodingApi.search(searchQuery.value)
      searchResults.value = results
    } catch (error) {
      console.error('搜索失败:', error)
      searchResults.value = []
    } finally {
      isSearching.value = false
    }
  }

  /**
   * 选择位置
   */
  const selectLocation = (location: GeocodeFeature) => {
    selectedLocation.value = location
    searchResults.value = []
    searchQuery.value = location.place_name
  }

  /**
   * 清空搜索
   */
  const clearSearch = () => {
    searchQuery.value = ''
    searchResults.value = []
    selectedLocation.value = null
  }

  return {
    searchQuery,
    searchResults,
    selectedLocation,
    isSearching,
    doSearch,
    selectLocation,
    clearSearch,
  }
}
