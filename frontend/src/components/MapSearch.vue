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
          <div class="result-name">{{ result.place_name }}</div>
          <div class="result-address">{{ result.text }}</div>
        </div>
      </div>
    </div>
    <div v-if="selectedLocation" class="location-line">
      <span class="loc-dot"></span>
      <span class="loc-name">{{ selectedLocation.place_name }}</span>
      <span class="loc-coord">{{ selectedLocation.center[0].toFixed(2) }}, {{ selectedLocation.center[1].toFixed(2) }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Search } from '@element-plus/icons-vue'
import { useMapStore } from '@/stores'
import { useGeocoding, useDebounce } from '@/composables'
import { API_CONFIG } from '@/config'
import type { GeocodeFeature } from '@/types/api'

const { t } = useI18n()
const mapStore = useMapStore()

// 定义事件
const emit = defineEmits<{
  'search-enter': []
  'location-selected': [location: GeocodeFeature]
}>()

// 使用地理编码组合式函数
const { searchQuery, searchResults, selectedLocation, isSearching, doSearch, selectLocation } =
  useGeocoding()

// 使用防抖函数
const { debouncedFn: debouncedSearch, cancel: cancelSearch } = useDebounce(
  doSearch,
  API_CONFIG.DEBOUNCE_DELAY
)

// 搜索处理函数，带防抖
const handleSearch = () => {
  if (!searchQuery.value || searchQuery.value.trim().length < API_CONFIG.SEARCH_MIN_LENGTH) {
    searchResults.value = []
    return
  }
  debouncedSearch()
}

// 回车搜索
const handleSearchEnter = () => {
  cancelSearch()
  if (!searchQuery.value || searchQuery.value.trim().length < API_CONFIG.SEARCH_MIN_LENGTH) {
    searchResults.value = []
    return
  }
  doSearch()
  // 触发事件，通知父组件进行图片搜索
  emit('search-enter')
}

// 选择位置并跳转地图
const handleSelectLocation = (location: GeocodeFeature) => {
  selectLocation(location)
  const [lng, lat] = location.center
  mapStore.setView([lng, lat], 14)
  // 触发地点选择事件，通知父组件进行图片搜索
  emit('location-selected', location)
}

// 监听搜索框清空
watch(searchQuery, newVal => {
  if (!newVal) {
    searchResults.value = []
  }
})

// 暴露给父组件的方法和属性
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
