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

  const doSearch = async (): Promise<GeocodeFeature[]> => {
    if (!validators.isValidSearchQuery(searchQuery.value, API_CONFIG.SEARCH_MIN_LENGTH)) {
      searchResults.value = []
      return []
    }

    isSearching.value = true
    try {
      const results = await geocodingApi.search(searchQuery.value)
      searchResults.value = results
      return results
    } catch (error) {
      console.error('Place search failed:', error)
      searchResults.value = []
      return []
    } finally {
      isSearching.value = false
    }
  }

  const selectLocation = (location: GeocodeFeature) => {
    selectedLocation.value = location
    searchResults.value = []
    searchQuery.value = location.place_name
  }

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
