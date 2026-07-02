<template>
  <div class="map-info">
    <MapSearch ref="mapSearchRef" @search-enter="handleSearchEnter" @location-selected="handleLocationSelected" />

    <div class="image-results">
      <div v-if="imageResults.length > 0" class="batch-toolbar">
        <span class="batch-count">
          {{ t('mapInfo.selectedImageCount', { selected: selectedSearchCount, total: imageResults.length }) }}
        </span>
        <div class="batch-actions">
          <button class="batch-link" :disabled="imageResults.length === 0" @click="selectAllSearch">
            {{ t('mapInfo.selectAllSearch') }}
          </button>
          <button class="batch-link" :disabled="selectedSearchCount === 0" @click="clearSearchSelection">
            {{ t('mapInfo.clearSearchSelection') }}
          </button>
        </div>
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
          <label class="image-check" @click.stop.prevent="toggleSearchSelect(index)">
            <input
              type="checkbox"
              :checked="selectedFlags[index]"
              readonly
            />
            <span class="image-check-mark" :class="{ 'image-check-mark--checked': selectedFlags[index] }"></span>
          </label>
          <div class="image-wrapper" @click="toggleSearchSelect(index)" @dblclick.stop="openImageViewer(index)">
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

    <ImageCollection
      :selected-images="selectedSearchImages"
      :local-files="localFiles"
      :total="totalBatchCount"
      :max="BATCH_MAX"
      :loading="pipelineLoading"
      :progress="pipelineProgressLine"
      :ready="colorSchemeStore.schemeGenerationReady"
      @upload="onLocalFilesPicked"
      @remove-search="removeSelectedSearchImage"
      @remove-local="removeLocalFile"
      @confirm="runVisionPipeline"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, unref, onMounted, onBeforeUnmount } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import MapSearch from './MapSearch.vue'
import ImageViewer from './ImageViewer.vue'
import ImageCollection from './ImageCollection.vue'
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
const imageResults = ref<ImageResult[]>([])
const selectedFlags = ref<boolean[]>([])
const localFiles = ref<File[]>([])
const isLoadingImages = ref(false)
const pipelineLoading = ref(false)
const pipelineProgressLine = ref('')
const currentLocationSlug = ref('')

const selectedSearchCount = computed(() => selectedFlags.value.filter(Boolean).length)
const totalBatchCount = computed(() => selectedSearchCount.value + localFiles.value.length)
const selectedSearchImages = computed(() =>
  imageResults.value
    .map((image, index) => ({ image, index }))
    .filter((_, index) => selectedFlags.value[index]),
)

function markSampleSetDirty() {
  if (!colorSchemeStore.schemeGenerationReady && !colorSchemeStore.lastPipelineJobId) return
  colorSchemeStore.setLastPipelineJobId(null)
  colorSchemeStore.setSchemeGenerationReady(false)
}

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
    markSampleSetDirty()
    return
  }

  const kw = keyword.trim()
  currentLocationSlug.value = slugifyLocation(kw)

  isLoadingImages.value = true
  imageResults.value = []
  markSampleSetDirty()

  try {
    const images = await imageApi.search(kw, IMAGE_CONFIG.SEARCH_POOL_COUNT)
    imageResults.value = images
    selectedFlags.value = images.map(() => false)
  } catch (error) {
    console.error('Failed to search images:', error)
    ElMessage.error(t('mapInfo.imageSearchFailed'))
  } finally {
    isLoadingImages.value = false
  }
}

const handleSearchEnter = async () => {
  // MapSearch exposes a Ref via defineExpose, so unwrap it before calling the API.
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
    'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="150"%3E%3Crect fill="%23ddd" width="200" height="150"/%3E%3Ctext fill="%23999" font-family="sans-serif" font-size="14" x="50%25" y="50%25" text-anchor="middle" dy=".3em"%3EImage unavailable%3C/text%3E%3C/svg%3E'
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
  markSampleSetDirty()
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
  markSampleSetDirty()
}

function clearSearchSelection() {
  selectedFlags.value = imageResults.value.map(() => false)
  markSampleSetDirty()
}

function removeSelectedSearchImage(index: number) {
  const next = [...selectedFlags.value]
  if (index >= 0 && index < next.length) {
    next[index] = false
    selectedFlags.value = next
    markSampleSetDirty()
  }
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
    markSampleSetDirty()
  }
}

function removeLocalFile(i: number) {
  localFiles.value = localFiles.value.filter((_, j) => j !== i)
  markSampleSetDirty()
}

type PipelineBuildEvent = CustomEvent<{
  resolve: (ok: boolean) => void
  reject: (reason?: unknown) => void
}>

const runVisionPipeline = async (): Promise<boolean> => {
  if (pipelineLoading.value) {
    ElMessage.warning(t('mapInfo.pipelineStarting'))
    return false
  }
  if (colorSchemeStore.schemeGenerationReady && colorSchemeStore.lastPipelineJobId) {
    return true
  }
  if (!currentLocationSlug.value) {
    ElMessage.warning(t('mapInfo.runPipelineDisabled'))
    return false
  }
  if (totalBatchCount.value === 0) {
    ElMessage.warning(t('mapInfo.noImagesSelected', { max: BATCH_MAX }))
    return false
  }
  if (totalBatchCount.value > BATCH_MAX) {
    ElMessage.warning(t('mapInfo.batchMaxReached', { max: BATCH_MAX }))
    return false
  }

  const urls = imageResults.value
    .filter((_, i) => selectedFlags.value[i])
    .map(img => String(img.url))
    .filter(Boolean)

  if (urls.length === 0 && localFiles.value.length === 0) {
    ElMessage.warning(t('mapInfo.noImagesSelected', { max: BATCH_MAX }))
    return false
  }

  pipelineLoading.value = true
  pipelineProgressLine.value = t('mapInfo.pipelineStarting')
  colorSchemeStore.setSchemeGenerationReady(false)
  try {
    pipelineProgressLine.value = t('mapInfo.pipelineSaving')
    const mergedIds: string[] = []

    const [uploaded, collected] = await Promise.all([
      localFiles.value.length > 0
        ? imageApi.upload(currentLocationSlug.value, localFiles.value)
        : Promise.resolve(null),
      urls.length > 0
        ? imageApi.collect({
            location: currentLocationSlug.value,
            urls,
          })
        : Promise.resolve(null),
    ])

    if (uploaded) {
      mergedIds.push(...uploaded.image_ids)
    }
    if (collected) {
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
      return false
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
    return true
  } catch (e) {
    colorSchemeStore.setLastPipelineJobId(null)
    colorSchemeStore.setSchemeGenerationReady(false)
    const msg = e instanceof Error ? e.message : String(e)
    ElMessage.error(msg)
    return false
  } finally {
    pipelineLoading.value = false
    pipelineProgressLine.value = ''
  }
}

async function handlePipelineBuildRequest(event: Event) {
  const e = event as PipelineBuildEvent
  try {
    e.detail.resolve(await runVisionPipeline())
  } catch (error) {
    e.detail.reject(error)
  }
}

onMounted(() => {
  window.addEventListener('placemap:build-samples', handlePipelineBuildRequest)
})

onBeforeUnmount(() => {
  window.removeEventListener('placemap:build-samples', handlePipelineBuildRequest)
})

watch(
  () => unref(mapSearchRef.value?.searchQuery) ?? '',
  newVal => {
    const s = typeof newVal === 'string' ? newVal.trim() : ''
    if (!s) {
      imageResults.value = []
      selectedFlags.value = []
      currentLocationSlug.value = ''
      localFiles.value = []
      markSampleSetDirty()
    }
  },
)
</script>

<style scoped>
.map-info {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background-color: #fafbfc;
  overflow: hidden;
}

.image-results {
  flex: 1;
  min-height: 0;
  padding: 0 16px;
  overflow-y: auto;
  overscroll-behavior: contain;
}

.batch-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0 12px;
  font-size: 12px;
  color: #8b8f98;
}

.batch-count {
  font-weight: 600;
  color: #1a1d23;
}

.batch-actions {
  display: flex;
  gap: 12px;
}

.batch-link {
  background: none;
  border: none;
  padding: 0;
  font-size: 12px;
  color: #5b6cf0;
  cursor: pointer;
  border-radius: 0;
}

.batch-link:hover {
  color: #4254d9;
}

.batch-link:disabled {
  color: #c4c7cf;
  cursor: default;
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
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.image-item {
  position: relative;
  cursor: pointer;
  border-radius: 8px;
  overflow: hidden;
  background: #f2f3f5;
  transition: box-shadow .18s;
}

.image-item--selected {
  box-shadow: 0 0 0 2px #5b6cf0;
}

.image-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.image-item--selected:hover {
  box-shadow: 0 0 0 2px #5b6cf0, 0 2px 8px rgba(91, 108, 240, 0.15);
}

.image-check {
  position: absolute;
  top: 5px;
  left: 5px;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  margin: 0;
  border-radius: 5px;
  cursor: pointer;
}

.image-check input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.image-check-mark {
  width: 18px;
  height: 18px;
  border-radius: 5px;
  background: rgba(255, 255, 255, 0.85);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: background .15s, box-shadow .15s;
}

.image-check-mark--checked {
  background: #5b6cf0;
  box-shadow: 0 1px 3px rgba(91, 108, 240, 0.3);
}

.image-check-mark--checked::after {
  content: '';
  position: absolute;
  left: 5px;
  top: 3px;
  width: 5px;
  height: 9px;
  border: solid #fff;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.image-check input,
.image-check-mark {
  cursor: pointer;
}

.image-wrapper {
  position: relative;
  width: 100%;
  padding-top: 68%;
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
}

.image-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 6px 8px;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.45), transparent);
  opacity: 0;
  transition: opacity .18s;
}

.image-item:hover .image-overlay {
  opacity: 1;
}

.image-title {
  color: #fff;
  font-size: 11px;
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
