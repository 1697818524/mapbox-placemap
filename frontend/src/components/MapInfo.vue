<template>
  <div class="map-info">
    <MapSearch ref="mapSearchRef" @search-enter="handleSearchEnter" @location-selected="handleLocationSelected" />

    <div class="image-results">
      <div class="image-results-header">
        <h3 class="image-results-title">{{ t('mapInfo.relatedImages') }}</h3>
        <el-tooltip :content="pipelineTooltipText" placement="top" :disabled="canSubmitPipeline && !pipelineLoading">
          <span>
            <el-button
              type="primary"
              size="small"
              :loading="pipelineLoading"
              :disabled="!canSubmitPipeline || isLoadingImages || pipelineLoading"
              @click="runVisionPipeline"
            >
              {{ t('mapInfo.runPipeline') }}
            </el-button>
          </span>
        </el-tooltip>
      </div>

      <div class="batch-toolbar">
        <span class="batch-count">{{ t('mapInfo.batchCount', { n: totalBatchCount, max: BATCH_MAX }) }}</span>
        <div class="batch-actions">
          <el-button text size="small" type="primary" :disabled="imageResults.length === 0" @click="selectAllSearch">
            {{ t('mapInfo.selectAllSearch') }}
          </el-button>
          <el-button text size="small" :disabled="selectedSearchCount === 0" @click="clearSearchSelection">
            {{ t('mapInfo.clearSearchSelection') }}
          </el-button>
        </div>
      </div>

      <div class="upload-row">
        <span class="upload-label">{{ t('mapInfo.localUpload') }}</span>
        <input
          ref="fileInputRef"
          type="file"
          class="hidden-input"
          multiple
          accept="image/*"
          @change="onLocalFilesPicked"
        />
        <el-button size="small" @click="openFilePicker">{{ t('mapInfo.chooseFiles') }}</el-button>
        <span class="upload-hint">{{ t('mapInfo.uploadHint', { max: BATCH_MAX }) }}</span>
      </div>
      <div v-if="localFiles.length > 0" class="local-files">
        <el-tag
          v-for="(f, i) in localFiles"
          :key="`${f.name}-${f.size}-${i}`"
          closable
          size="small"
          class="file-tag"
          @close="removeLocalFile(i)"
        >
          {{ f.name }}
        </el-tag>
      </div>

      <div v-if="pipelineLoading && pipelineProgressLine" class="pipeline-progress">
        {{ pipelineProgressLine }}
      </div>

      <div v-if="isLoadingImages" class="image-loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>{{ t('mapInfo.loadingImages') }}</span>
      </div>
      <div v-else-if="imageResults.length > 0" class="image-grid">
        <div
          v-for="(image, index) in imageResults"
          :key="index"
          class="image-item"
          :class="{ 'image-item--selected': selectedFlags[index] }"
        >
          <label class="image-check" @click.stop>
            <input
              type="checkbox"
              :checked="selectedFlags[index]"
              @click.prevent="toggleSearchSelect(index)"
            />
          </label>
          <div class="image-wrapper" @click="openImageViewer(index)">
            <img
              :src="getImageProxyUrl(image.thumbnail || image.url)"
              :alt="image.title || t('mapInfo.image')"
              referrerpolicy="no-referrer"
              @error="handleImageError($event)"
              loading="lazy"
            />
            <div class="image-overlay">
              <span class="image-title">{{ image.title || t('mapInfo.image') }}</span>
            </div>
          </div>
        </div>
      </div>

      <ImageViewer
        v-if="showImageViewer"
        :images="imageResults"
        :current-index="currentImageIndex"
        @close="closeImageViewer"
        @prev="prevImage"
        @next="nextImage"
      />
      <div v-else-if="!isLoadingImages && imageResults.length === 0" class="image-empty">
        <span>{{ t('mapInfo.imageSearchPlaceholder') }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, unref } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import MapSearch from './MapSearch.vue'
import ImageViewer from './ImageViewer.vue'
import { imageApi, pipelineApi, isSchemeGenerationReady, getImageProxyUrl } from '@/api'
import { API_CONFIG, IMAGE_CONFIG } from '@/config'
import { slugifyLocation } from '@/utils'
import { useColorSchemeStore } from '@/stores'
import type { ImageResult, GeocodeFeature } from '@/types/api'
import type { PipelineJob } from '@/api/pipeline'

const BATCH_MAX = IMAGE_CONFIG.BATCH_MAX

const { t } = useI18n()
const colorSchemeStore = useColorSchemeStore()

const mapSearchRef = ref<InstanceType<typeof MapSearch> | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const imageResults = ref<ImageResult[]>([])
const selectedFlags = ref<boolean[]>([])
const localFiles = ref<File[]>([])
const isLoadingImages = ref(false)
const pipelineLoading = ref(false)
const pipelineProgressLine = ref('')
const currentLocationSlug = ref('')

const selectedSearchCount = computed(() => selectedFlags.value.filter(Boolean).length)
const totalBatchCount = computed(() => selectedSearchCount.value + localFiles.value.length)

const canSubmitPipeline = computed(() => {
  if (!currentLocationSlug.value.trim()) return false
  if (totalBatchCount.value < 1 || totalBatchCount.value > BATCH_MAX) return false
  return true
})

const pipelineTooltipText = computed(() => {
  if (!currentLocationSlug.value.trim()) return t('mapInfo.runPipelineDisabled')
  if (totalBatchCount.value === 0) return t('mapInfo.noImagesSelected', { max: BATCH_MAX })
  if (totalBatchCount.value > BATCH_MAX) return t('mapInfo.batchMaxReached', { max: BATCH_MAX })
  return t('mapInfo.runPipelineDisabled')
})

function pipelineStageLabel(job: PipelineJob): string {
  const s = job.current_stage
  if (s) {
    return t(`mapInfo.stages.${s}`)
  }
  if (job.status === 'queued') {
    return t('mapInfo.stages.queued')
  }
  return t('mapInfo.stages.running')
}

function updatePipelineProgressFromJob(job: PipelineJob) {
  const stage = pipelineStageLabel(job)
  const p = Math.round(job.progress ?? 0)
  pipelineProgressLine.value = t('mapInfo.pipelineProgress', { stage, progress: p })
}

const showImageViewer = ref(false)
const currentImageIndex = ref(0)

const searchImages = async (keyword: string) => {
  if (!keyword || keyword.trim().length < API_CONFIG.SEARCH_MIN_LENGTH) {
    imageResults.value = []
    selectedFlags.value = []
    currentLocationSlug.value = ''
    localFiles.value = []
    return
  }

  const kw = keyword.trim()
  currentLocationSlug.value = slugifyLocation(kw)

  isLoadingImages.value = true
  imageResults.value = []

  try {
    const images = await imageApi.search(kw, IMAGE_CONFIG.SEARCH_POOL_COUNT)
    imageResults.value = images
    selectedFlags.value = images.map(() => false)
  } catch (error) {
    console.error('搜索图片失败:', error)
    ElMessage.error(t('mapInfo.imageSearchFailed'))
  } finally {
    isLoadingImages.value = false
  }
}

const handleSearchEnter = async () => {
  // MapSearch 通过 defineExpose 暴露的 searchQuery 是 Ref<string>，必须 unref 后再传给接口
  const q = unref(mapSearchRef.value?.searchQuery)
  const keyword = typeof q === 'string' ? q : ''
  if (keyword.trim()) {
    await searchImages(keyword)
  }
}

const handleLocationSelected = async (location: GeocodeFeature) => {
  const searchKeyword = location.place_name || location.text || ''
  if (searchKeyword) {
    await searchImages(searchKeyword)
  }
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.src =
    'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="150"%3E%3Crect fill="%23ddd" width="200" height="150"/%3E%3Ctext fill="%23999" font-family="sans-serif" font-size="14" x="50%25" y="50%25" text-anchor="middle" dy=".3em"%3E图片加载失败%3C/text%3E%3C/svg%3E'
}

const openImageViewer = (index: number) => {
  currentImageIndex.value = index
  showImageViewer.value = true
}

const closeImageViewer = () => {
  showImageViewer.value = false
}

const prevImage = () => {
  if (currentImageIndex.value > 0) {
    currentImageIndex.value--
  }
}

const nextImage = () => {
  if (currentImageIndex.value < imageResults.value.length - 1) {
    currentImageIndex.value++
  }
}

function toggleSearchSelect(index: number) {
  const next = [...selectedFlags.value]
  if (!next[index]) {
    if (totalBatchCount.value >= BATCH_MAX) {
      ElMessage.warning(t('mapInfo.batchMaxReached', { max: BATCH_MAX }))
      return
    }
    next[index] = true
  } else {
    next[index] = false
  }
  selectedFlags.value = next
}

function selectAllSearch() {
  const cap = BATCH_MAX - localFiles.value.length
  if (cap <= 0) {
    ElMessage.warning(t('mapInfo.batchMaxReached', { max: BATCH_MAX }))
    return
  }
  const next = imageResults.value.map(() => false)
  let used = 0
  for (let i = 0; i < next.length && used < cap; i++) {
    next[i] = true
    used++
  }
  selectedFlags.value = next
}

function clearSearchSelection() {
  selectedFlags.value = imageResults.value.map(() => false)
}

function openFilePicker() {
  fileInputRef.value?.click()
}

function onLocalFilesPicked(e: Event) {
  const input = e.target as HTMLInputElement
  const picked = input.files ? Array.from(input.files) : []
  input.value = ''
  let remaining = BATCH_MAX - selectedSearchCount.value
  for (const f of picked) {
    if (!f.type.startsWith('image/')) {
      continue
    }
    if (remaining <= 0) {
      ElMessage.warning(t('mapInfo.batchMaxReached', { max: BATCH_MAX }))
      break
    }
    const dup = localFiles.value.some(x => x.name === f.name && x.size === f.size)
    if (dup) continue
    localFiles.value.push(f)
    remaining--
  }
}

function removeLocalFile(i: number) {
  localFiles.value = localFiles.value.filter((_, j) => j !== i)
}

const runVisionPipeline = async () => {
  if (!currentLocationSlug.value) {
    ElMessage.warning(t('mapInfo.runPipelineDisabled'))
    return
  }
  if (totalBatchCount.value === 0) {
    ElMessage.warning(t('mapInfo.noImagesSelected', { max: BATCH_MAX }))
    return
  }
  if (totalBatchCount.value > BATCH_MAX) {
    ElMessage.warning(t('mapInfo.batchMaxReached', { max: BATCH_MAX }))
    return
  }

  const urls = imageResults.value
    .filter((_, i) => selectedFlags.value[i])
    .map(img => String(img.url))
    .filter(Boolean)

  if (urls.length === 0 && localFiles.value.length === 0) {
    ElMessage.warning(t('mapInfo.noImagesSelected', { max: BATCH_MAX }))
    return
  }

  pipelineLoading.value = true
  pipelineProgressLine.value = t('mapInfo.pipelineStarting')
  colorSchemeStore.setSchemeGenerationReady(false)
  try {
    pipelineProgressLine.value = t('mapInfo.pipelineSaving')
    const mergedIds: string[] = []

    if (localFiles.value.length > 0) {
      const uploaded = await imageApi.upload(currentLocationSlug.value, localFiles.value)
      mergedIds.push(...uploaded.image_ids)
    }
    if (urls.length > 0) {
      const collected = await imageApi.collect({
        location: currentLocationSlug.value,
        urls,
      })
      mergedIds.push(...collected.image_ids)
    }

    if (mergedIds.length === 0) {
      throw new Error(t('mapInfo.noImagesSelected', { max: BATCH_MAX }))
    }
    if (mergedIds.length > BATCH_MAX) {
      throw new Error(t('mapInfo.batchMaxReached', { max: BATCH_MAX }))
    }

    const created = await pipelineApi.createJob({
      location: currentLocationSlug.value,
      image_ids: mergedIds,
    })

    await pipelineApi.runJob(created.job_id)
    const final = await pipelineApi.waitForTerminal(created.job_id, {
      intervalMs: 2000,
      timeoutMs: 45 * 60 * 1000,
      onProgress: updatePipelineProgressFromJob,
    })

    if (final.status === 'failed') {
      colorSchemeStore.setLastPipelineJobId(null)
      colorSchemeStore.setSchemeGenerationReady(false)
      const msg = final.error_message || final.error_code || 'unknown'
      ElMessage.error(t('mapInfo.pipelineFailed', { msg }))
      return
    }

    colorSchemeStore.setLastPipelineJobId(created.job_id)
    const jobDetail = await pipelineApi.getJob(created.job_id)
    colorSchemeStore.setSchemeGenerationReady(isSchemeGenerationReady(jobDetail))
    try {
      const { schemes } = await pipelineApi.getJobSchemes(created.job_id)
      if (schemes.length > 0) {
        colorSchemeStore.setColorSchemes(schemes)
      }
    } catch {
      /* 方案文件缺失时不阻断成功提示 */
    }
    ElMessage.success(t('mapInfo.pipelineSuccess'))
    localFiles.value = []
    selectedFlags.value = imageResults.value.map(() => false)
  } catch (e) {
    colorSchemeStore.setLastPipelineJobId(null)
    colorSchemeStore.setSchemeGenerationReady(false)
    const msg = e instanceof Error ? e.message : String(e)
    ElMessage.error(msg)
  } finally {
    pipelineLoading.value = false
    pipelineProgressLine.value = ''
  }
}

watch(
  () => unref(mapSearchRef.value?.searchQuery) ?? '',
  newVal => {
    const s = typeof newVal === 'string' ? newVal.trim() : ''
    if (!s) {
      imageResults.value = []
      selectedFlags.value = []
      currentLocationSlug.value = ''
      localFiles.value = []
    }
  },
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

.pipeline-progress {
  font-size: 12px;
  color: #606266;
  margin: -8px 0 12px;
  line-height: 1.4;
}

.image-results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.batch-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 12px;
  color: #606266;
}

.batch-count {
  font-weight: 600;
  color: #303133;
}

.batch-actions {
  display: flex;
  gap: 4px;
}

.upload-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 12px;
}

.upload-label {
  color: #606266;
}

.upload-hint {
  color: #909399;
  font-size: 11px;
}

.hidden-input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  pointer-events: none;
}

.local-files {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.file-tag {
  max-width: 100%;
}

.image-results-title {
  margin: 0;
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
}

.image-item {
  position: relative;
  cursor: pointer;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f7fa;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
  outline: 2px solid transparent;
}

.image-item--selected {
  outline-color: #4264fb;
}

.image-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.image-check {
  position: absolute;
  top: 6px;
  left: 6px;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  margin: 0;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 4px;
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
}

.image-check input {
  margin: 0;
  cursor: pointer;
}

.image-wrapper {
  position: relative;
  width: 100%;
  padding-top: 75%;
  overflow: hidden;
}

.image-wrapper img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
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

@media (max-width: 768px) {
  .image-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }
}
</style>
