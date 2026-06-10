<template>
  <section class="image-collection">
    <div class="collection-head">
      <div>
        <h3>图片集</h3>
        <p>{{ total }} / {{ max }} 张，用于自动构建样本集</p>
      </div>
      <div class="collection-actions">
        <input
          ref="fileInputRef"
          type="file"
          class="hidden-input"
          multiple
          accept="image/*"
          @change="onPicked"
        />
        <el-button size="small" @click="fileInputRef?.click()">上传图片</el-button>
      </div>
    </div>

    <div class="collection-status" :class="{ active: loading }">
      {{ loading ? progress : '当地图片和上传图片会一起组成最终图片集' }}
    </div>

    <div v-if="total === 0" class="collection-empty">
      先从搜索结果中选择图片，或上传自己的图片。
    </div>

    <div v-else class="collection-grid">
      <div
        v-for="item in selectedImages"
        :key="`remote-${item.index}`"
        class="collection-card"
      >
        <img
          :src="getImageProxyUrl(item.image.thumbnail || item.image.url)"
          :alt="item.image.title || '当地图片'"
          referrerpolicy="no-referrer"
          loading="lazy"
        />
        <span class="source-pill">当地</span>
        <button class="remove-btn" type="button" @click="$emit('remove-search', item.index)">×</button>
      </div>

      <div v-for="item in localPreviewItems" :key="item.key" class="collection-card">
        <img :src="item.url" :alt="item.file.name" loading="lazy" />
        <span class="source-pill source-pill--local">上传</span>
        <button class="remove-btn" type="button" @click="$emit('remove-local', item.index)">×</button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { getImageProxyUrl } from '@/api'
import type { ImageResult } from '@/types/api'

const props = defineProps<{
  selectedImages: Array<{ image: ImageResult; index: number }>
  localFiles: File[]
  total: number
  max: number
  loading: boolean
  progress: string
}>()

const emit = defineEmits<{
  upload: [event: Event]
  'remove-search': [index: number]
  'remove-local': [index: number]
}>()

const fileInputRef = ref<HTMLInputElement | null>(null)
const objectUrls = ref<string[]>([])

const localPreviewItems = computed(() =>
  props.localFiles.map((file, index) => ({
    file,
    index,
    url: objectUrls.value[index] || '',
    key: `${file.name}-${file.size}-${file.lastModified}-${index}`,
  })),
)

function revokeUrls() {
  objectUrls.value.forEach(url => URL.revokeObjectURL(url))
  objectUrls.value = []
}

watch(
  () => props.localFiles,
  files => {
    revokeUrls()
    objectUrls.value = files.map(file => URL.createObjectURL(file))
  },
  { immediate: true, deep: true },
)

function onPicked(event: Event) {
  emit('upload', event)
}

onBeforeUnmount(revokeUrls)
</script>

<style scoped>
.image-collection {
  margin-top: 14px;
  padding: 14px;
  border: 1px solid #e6ebf2;
  border-radius: 10px;
  background: #f8fafc;
}

.collection-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.collection-head h3 {
  margin: 0;
  font-size: 15px;
  color: #1f2937;
}

.collection-head p {
  margin: 4px 0 0;
  font-size: 12px;
  color: #667085;
}

.collection-actions {
  flex-shrink: 0;
}

.hidden-input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  pointer-events: none;
}

.collection-status {
  margin-top: 10px;
  font-size: 12px;
  color: #667085;
}

.collection-status.active {
  color: #4264fb;
  font-weight: 600;
}

.collection-empty {
  margin-top: 12px;
  padding: 18px 12px;
  border: 1px dashed #d7dee8;
  border-radius: 8px;
  color: #8a94a6;
  font-size: 12px;
  text-align: center;
  background: #fff;
}

.collection-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-top: 12px;
}

.collection-card {
  position: relative;
  overflow: hidden;
  border-radius: 8px;
  aspect-ratio: 4 / 3;
  background: #eef2f7;
}

.collection-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.source-pill {
  position: absolute;
  left: 6px;
  bottom: 6px;
  padding: 2px 6px;
  border-radius: 999px;
  color: #fff;
  font-size: 11px;
  background: rgba(66, 100, 251, 0.88);
}

.source-pill--local {
  background: rgba(22, 163, 74, 0.88);
}

.remove-btn {
  position: absolute;
  top: 5px;
  right: 5px;
  width: 22px;
  height: 22px;
  border: 0;
  border-radius: 50%;
  color: #1f2937;
  background: rgba(255, 255, 255, 0.92);
  cursor: pointer;
  line-height: 20px;
}
</style>
