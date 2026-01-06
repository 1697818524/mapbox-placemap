<template>
  <div class="map-info">
    <!-- 搜索组件 -->
    <MapSearch ref="mapSearchRef" @search-enter="handleSearchEnter" @location-selected="handleLocationSelected" />

    <!-- 百度图片搜索结果 -->
    <div class="image-results">
      <h3 class="image-results-title">{{ t('mapInfo.relatedImages') }}</h3>
      <div v-if="isLoadingImages" class="image-loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>{{ t('mapInfo.loadingImages') }}</span>
      </div>
      <div v-else-if="imageResults.length > 0" class="image-grid">
        <div
          v-for="(image, index) in imageResults"
          :key="index"
          class="image-item"
          @click="openImageViewer(index)"
        >
          <div class="image-wrapper">
            <img
              :src="image.thumbnail || image.url"
              :alt="image.title || t('mapInfo.image')"
              @error="handleImageError($event)"
              loading="lazy"
            />
            <div class="image-overlay">
              <span class="image-title">{{ image.title || t('mapInfo.image') }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 图片查看器 -->
      <ImageViewer
        v-if="showImageViewer"
        :images="imageResults"
        :current-index="currentImageIndex"
        @close="closeImageViewer"
        @prev="prevImage"
        @next="nextImage"
      />
      <div v-else class="image-empty">
        <span>{{ t('mapInfo.imageSearchPlaceholder') }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import MapSearch from './MapSearch.vue'
import ImageViewer from './ImageViewer.vue'
import { imageApi } from '@/api'
import { API_CONFIG, IMAGE_CONFIG } from '@/config'
import type { ImageResult, GeocodeFeature } from '@/types/api'

const { t } = useI18n()

const mapSearchRef = ref<InstanceType<typeof MapSearch> | null>(null)
const imageResults = ref<ImageResult[]>([])
const isLoadingImages = ref(false)

// 图片查看器相关状态
const showImageViewer = ref(false)
const currentImageIndex = ref(0)

// 搜索图片的通用函数
const searchImages = async (keyword: string) => {
  if (!keyword || keyword.trim().length < API_CONFIG.SEARCH_MIN_LENGTH) {
    imageResults.value = []
    return
  }

  isLoadingImages.value = true
  imageResults.value = []

  try {
    const images = await imageApi.search(keyword, IMAGE_CONFIG.GRID_COLUMNS * 3)
    imageResults.value = images
  } catch (error) {
    console.error('搜索图片失败:', error)
    ElMessage.error(t('mapInfo.imageSearchFailed'))
  } finally {
    isLoadingImages.value = false
  }
}

// 处理回车搜索事件
const handleSearchEnter = async () => {
  const searchQuery = mapSearchRef.value?.searchQuery
  if (searchQuery) {
    await searchImages(searchQuery)
  }
}

// 处理地点选择事件（点击搜索结果时自动搜索图片）
const handleLocationSelected = async (location: GeocodeFeature) => {
  // 使用地点的名称进行图片搜索
  // 优先使用 place_name（完整地址），如果没有则使用 text（地点名称）
  const searchKeyword = location.place_name || location.text || ''
  if (searchKeyword) {
    await searchImages(searchKeyword)
  }
}

// 处理图片加载错误
const handleImageError = (event: Event) => {
  // 设置默认占位图
  const img = event.target as HTMLImageElement
  img.src =
    'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="150"%3E%3Crect fill="%23ddd" width="200" height="150"/%3E%3Ctext fill="%23999" font-family="sans-serif" font-size="14" x="50%25" y="50%25" text-anchor="middle" dy=".3em"%3E图片加载失败%3C/text%3E%3C/svg%3E'
}

// 打开图片查看器
const openImageViewer = (index: number) => {
  currentImageIndex.value = index
  showImageViewer.value = true
}

// 关闭图片查看器
const closeImageViewer = () => {
  showImageViewer.value = false
}

// 上一张图片
const prevImage = () => {
  if (currentImageIndex.value > 0) {
    currentImageIndex.value--
  }
}

// 下一张图片
const nextImage = () => {
  if (currentImageIndex.value < imageResults.value.length - 1) {
    currentImageIndex.value++
  }
}

// 监听搜索框变化，清空图片结果
watch(
  () => mapSearchRef.value?.searchQuery,
  newVal => {
    if (!newVal || newVal.trim().length === 0) {
      imageResults.value = []
    }
  }
)
</script>

<style scoped>
.map-info {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #fff;
  overflow-y: auto;
}

.image-results {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

.image-results-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.image-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px;
  color: #909399;
  font-size: 14px;
}

.image-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #909399;
  font-size: 14px;
  text-align: center;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  /* 三行布局，每行3张图片 */
}

.image-item {
  cursor: pointer;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f7fa;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}

.image-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.image-wrapper {
  position: relative;
  width: 100%;
  padding-top: 75%; /* 4:3 宽高比 */
  overflow: hidden;
}

.image-wrapper img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover; /* 保持宽高比，裁剪多余部分 */
  object-position: center;
  transition: transform 0.3s;
}

.image-item:hover .image-wrapper img {
  transform: scale(1.05);
}

.image-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.7), transparent);
  padding: 12px 8px 8px;
  opacity: 0;
  transition: opacity 0.2s;
}

.image-item:hover .image-overlay {
  opacity: 1;
}

.image-title {
  color: #fff;
  font-size: 12px;
  font-weight: 500;
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .image-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }
}
</style>
