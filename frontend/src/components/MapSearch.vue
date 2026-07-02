<template>
  <div class="map-search">
    <div class="search-container">
      <el-input
        v-model="searchQuery"
        :placeholder="t('mapInfo.searchPlaceholder')"
        class="search-input"
        clearable
        :loading="isSearching"
        @input="handleSearch"
        @keyup.enter="handleSearchEnter"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <div v-if="searchResults.length > 0" class="search-results">
        <div
          v-for="(result, index) in searchResults"
          :key="index"
          class="search-result-item"
          @click="handleSelectLocation(result)"
        >
          <div class="result-name">{{ result.name || result.text }}</div>
          <div class="result-address">
            <span v-if="result.provider" class="provider-badge">{{ result.provider }}</span>
            <span>{{ result.address || result.place_name }}</span>
          </div>
        </div>
      </div>
    </div>
    <div v-if="selectedLocation" class="location-line">
      <span class="loc-dot"></span>
      <span class="loc-name">{{ selectedLocation.place_name }}</span>
      <span class="loc-coord">
        {{ selectedLocation.center[0].toFixed(2) }}, {{ selectedLocation.center[1].toFixed(2) }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useMapStore } from '@/stores'
import { useGeocoding, useDebounce } from '@/composables'
import { API_CONFIG } from '@/config'
import type { GeocodeFeature } from '@/types/api'

const { t } = useI18n()
const mapStore = useMapStore()

const emit = defineEmits<{
  'search-enter': []
  'location-selected': [location: GeocodeFeature]
}>()

const { searchQuery, searchResults, selectedLocation, isSearching, doSearch, selectLocation } =
  useGeocoding()

const { debouncedFn: debouncedSearch, cancel: cancelSearch } = useDebounce(
  doSearch,
  API_CONFIG.DEBOUNCE_DELAY,
)

const handleSearch = () => {
  if (!searchQuery.value || searchQuery.value.trim().length < API_CONFIG.SEARCH_MIN_LENGTH) {
    searchResults.value = []
    return
  }
  debouncedSearch()
}

const handleSearchEnter = async () => {
  cancelSearch()
  if (!searchQuery.value || searchQuery.value.trim().length < API_CONFIG.SEARCH_MIN_LENGTH) {
    searchResults.value = []
    return
  }

  const results = await doSearch()
  const first = results[0]
  if (first?.center) {
    handleSelectLocation(first)
    return
  }

  ElMessage.warning(t('mapInfo.noJumpablePlace'))
  emit('search-enter')
}

const handleSelectLocation = (location: GeocodeFeature) => {
  selectLocation(location)
  const [lng, lat] = location.center
  mapStore.setView([lng, lat], 14)
  emit('location-selected', location)
}

watch(searchQuery, newVal => {
  if (!newVal) {
    searchResults.value = []
  }
})

defineExpose({
  selectedLocation,
  searchQuery,
  handleSearchEnter,
})
</script>

<style scoped>
.map-search {
  padding: 14px 16px 12px;
  background-color: #fff;
}

.search-container {
  position: relative;
  margin-bottom: 0;
}

.search-input {
  width: 100%;
}

.search-input :deep(.el-input__wrapper) {
  min-height: 36px;
  border-radius: 8px;
  box-shadow: 0 0 0 1px #e1e4e8 inset;
  background: #f6f8fa;
  transition: box-shadow .2s, background .2s;
}

.search-input :deep(.el-input__wrapper:hover) {
  background: #fff;
}

.search-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #5b6cf0 inset;
  background: #fff;
}

.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #fff;
  border: 1px solid #e8eaed;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  z-index: 1000;
  max-height: 280px;
  overflow-y: auto;
  margin-top: 6px;
}

.search-result-item {
  padding: 10px 14px;
  cursor: pointer;
  transition: background-color .15s;
}

.search-result-item:hover {
  background-color: #f6f8fa;
}

.search-result-item + .search-result-item {
  border-top: 1px solid #f3f4f6;
}

.result-name {
  font-weight: 600;
  color: #1a1d23;
  font-size: 13px;
}

.result-address {
  margin-top: 2px;
  font-size: 12px;
  color: #8b8f98;
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.result-address span:last-child {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.provider-badge {
  flex-shrink: 0;
  padding: 1px 5px;
  border-radius: 4px;
  background: #eef2ff;
  color: #4f46e5;
  font-size: 10px;
  line-height: 16px;
  text-transform: uppercase;
}

.location-line {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #6b6f78;
  white-space: nowrap;
  overflow: hidden;
}

.loc-dot {
  flex-shrink: 0;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #5b6cf0;
}

.loc-name {
  font-weight: 600;
  color: #1a1d23;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.loc-coord {
  flex-shrink: 0;
  color: #8b8f98;
}
</style>
