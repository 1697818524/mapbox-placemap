<template>
  <div class="map-info">
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
          @click="selectLocation(result)"
        >
          <div class="result-name">{{ result.place_name }}</div>
          <div class="result-address">{{ result.text }}</div>
        </div>
      </div>
    </div>
    <div v-if="selectedLocation" class="location-info">
      <h3>{{ t('mapInfo.selectedLocation') }}</h3>
      <p><strong>{{ t('mapInfo.name') }}:</strong> {{ selectedLocation.place_name }}</p>
      <p>
        <strong>{{ t('mapInfo.coordinates') }}:</strong>
        {{ selectedLocation.center[0].toFixed(4) }}, {{ selectedLocation.center[1].toFixed(4) }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import { Search } from '@element-plus/icons-vue'
import { useMapStore } from '@/stores'

const { t } = useI18n()
const mapStore = useMapStore()

type GeocodeFeature = {
  place_name: string
  text: string
  center: [number, number]
}

const searchQuery = ref('')
const searchResults = ref<GeocodeFeature[]>([])
const selectedLocation = ref<GeocodeFeature | null>(null)
const searchTimeout = ref<NodeJS.Timeout | null>(null)
const isSearching = ref(false)

// Mapbox Geocoding API 配置
const MAPBOX_TOKEN = 'pk.eyJ1IjoiZGYweGV3YyIsImEiOiJjbTNoamh0NnMwZzZ6MnRwcXJkbWUxM2syIn0.eE5V7j0-uNb4WiwG2hXs0w'
const GEOCODING_API_URL = 'https://api.mapbox.com/geocoding/v5/mapbox.places'

const doSearch = async () => {
  isSearching.value = true
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 5000)
  try {
    const response = await fetch(
      `${GEOCODING_API_URL}/${encodeURIComponent(searchQuery.value)}.json?access_token=${MAPBOX_TOKEN}&limit=5`,
      { signal: controller.signal }
    )
    clearTimeout(timeoutId)
    const data = await response.json()
    searchResults.value = data.features || []
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      console.error('搜索超时')
    } else {
      console.error('搜索错误:', error)
    }
    searchResults.value = []
  } finally {
    isSearching.value = false
  }
}

// 搜索处理函数，带防抖
const handleSearch = () => {
  if (searchTimeout.value) clearTimeout(searchTimeout.value)

  if (!searchQuery.value || searchQuery.value.trim().length < 2) {
    searchResults.value = []
    return
  }

  searchTimeout.value = setTimeout(doSearch, 200)
}

// 回车搜索
const handleSearchEnter = () => {
  if (searchTimeout.value) clearTimeout(searchTimeout.value)
  if (!searchQuery.value || searchQuery.value.trim().length < 2) {
    searchResults.value = []
    return
  }
  doSearch()
}

// 选择位置
const selectLocation = (location: GeocodeFeature) => {
  selectedLocation.value = location
  searchResults.value = []
  searchQuery.value = location.place_name

  const [lng, lat] = location.center
  mapStore.setView([lng, lat], 14)
}

// 监听搜索框清空
watch(searchQuery, (newVal) => {
  if (!newVal) {
    searchResults.value = []
  }
})

onBeforeUnmount(() => {
  if (searchTimeout.value) clearTimeout(searchTimeout.value)
})
</script>

<style scoped>
.map-info {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 16px;
  background-color: #fff;
  overflow-y: auto;
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
