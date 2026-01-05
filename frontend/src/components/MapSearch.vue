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
    <div v-if="selectedLocation" class="location-info">
      <h3>{{ t('mapInfo.selectedLocation') }}</h3>
      <p>
        <strong>{{ t('mapInfo.name') }}:</strong> {{ selectedLocation.place_name }}
      </p>
      <p>
        <strong>{{ t('mapInfo.coordinates') }}:</strong>
        {{ selectedLocation.center[0].toFixed(4) }}, {{ selectedLocation.center[1].toFixed(4) }}
      </p>
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
  padding: 16px;
  background-color: #fff;
}

.search-container {
  position: relative;
  margin-bottom: 16px;
}

.search-input {
  width: 100%;
}

.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  z-index: 1000;
  max-height: 300px;
  overflow-y: auto;
  margin-top: 4px;
}

.search-result-item {
  padding: 12px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s;
}

.search-result-item:hover {
  background-color: #f5f7fa;
}

.search-result-item:last-child {
  border-bottom: none;
}

.result-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
  font-size: 14px;
}

.result-address {
  font-size: 12px;
  color: #909399;
}

.location-info {
  margin-top: 16px;
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.location-info h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #303133;
}

.location-info p {
  margin: 8px 0;
  font-size: 14px;
  color: #606266;
}

.location-info strong {
  color: #303133;
}
</style>
