<template>
  <section class="image-collection">
    <div class="collection-divider"></div>

    <div class="collection-head">
      <span class="collection-label">
        {{ t('imageCollection.title') }} <strong>{{ total }}</strong><span class="label-dim">/{{ max }}</span>
      </span>
      <span v-if="!loading && ready" class="badge-done">{{ t('imageCollection.ready') }}</span>
    </div>

    <div v-if="total === 0" class="collection-empty">
      {{ t('imageCollection.empty') }}
    </div>

    <div v-else class="collection-grid" :class="{ 'grid-3col': total >= 5 }">
      <div
        v-for="item in selectedImages"
        :key="`remote-${item.index}`"
        class="collection-card"
      >
        <img
          :src="getImageProxyUrl(item.image.thumbnail || item.image.url)"
          :alt="item.image.title || t('imageCollection.localImageAlt')"
          referrerpolicy="no-referrer"
          loading="lazy"
        />
        <button class="remove-btn" type="button" @click="$emit('remove-search', item.index)" :title="t('common.remove')">
          <span class="remove-icon"></span>
        </button>
      </div>

      <div v-for="item in localPreviewItems" :key="item.key" class="collection-card">
        <img :src="item.url" :alt="item.file.name" loading="lazy" />
        <button class="remove-btn" type="button" @click="$emit('remove-local', item.index)" :title="t('common.remove')">
          <span class="remove-icon"></span>
        </button>
      </div>
    </div>

    <p class="collection-status" :class="{ active: loading, ready }">
      {{ loading ? progress : ready ? '' : '' }}
    </p>

    <div class="collection-actions">
      <input
        ref="fileInputRef"
        type="file"
        class="hidden-input"
        multiple
        accept="image/*"
        @change="onPicked"
      />
      <button class="act-upload" @click="fileInputRef?.click()">
        <span class="act-icon">+</span> {{ t('imageCollection.upload') }}
      </button>
      <button
        class="act-confirm"
        :disabled="total === 0 || loading || ready"
        @click="$emit('confirm')"
      >
        {{ ready ? t('imageCollection.extracted') : loading ? t('imageCollection.extracting') : t('imageCollection.extract') }}
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { getImageProxyUrl } from '@/api'
import type { ImageResult } from '@/types/api'

const props = defineProps<{
  selectedImages: Array<{ image: ImageResult; index: number }>
  localFiles: File[]
  total: number
  max: number
  loading: boolean
  progress: string
  ready: boolean
}>()

const emit = defineEmits<{
  upload: [event: Event]
  'remove-search': [index: number]
  'remove-local': [index: number]
  confirm: []
}>()

const { t } = useI18n()
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
  flex-shrink: 0;
  padding: 0 16px 14px;
  background: #fafbfc;
}

.collection-divider {
  height: 1px;
  background: #eceef2;
  margin-bottom: 12px;
}

.collection-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.collection-label {
  font-size: 13px;
  color: #1a1d23;
}

.collection-label strong {
  font-weight: 700;
}

.label-dim {
  font-weight: 400;
  color: #8b8f98;
}

.badge-done {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: #e6f7ed;
  color: #16834a;
  font-weight: 600;
}

.collection-empty {
  padding: 14px 0;
  font-size: 12px;
  color: #8b8f98;
}

.collection-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
}

.collection-grid.grid-3col {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.collection-card {
  position: relative;
  overflow: hidden;
  border-radius: 8px;
  aspect-ratio: 4 / 3;
  background: #ebeef2;
}

.collection-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.remove-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  border: 0;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.45);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity .15s;
}

.remove-icon {
  position: relative;
  width: 10px;
  height: 10px;
}

.remove-icon::before,
.remove-icon::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  width: 100%;
  height: 1.5px;
  background: #fff;
  border-radius: 1px;
}

.remove-icon::before {
  transform: rotate(45deg);
}

.remove-icon::after {
  transform: rotate(-45deg);
}

.collection-card:hover .remove-btn {
  opacity: 1;
}

.collection-status {
  margin: 8px 0 0;
  font-size: 12px;
  color: #8b8f98;
  min-height: 0;
}

.collection-status.active {
  color: #5b6cf0;
  font-weight: 600;
}

.collection-status.ready {
  color: #16834a;
}

.collection-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.act-upload {
  flex: 0 0 auto;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid #dde0e5;
  border-radius: 8px;
  background: #fff;
  color: #1a1d23;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: border-color .15s, background .15s;
}

.act-upload:hover {
  border-color: #5b6cf0;
  background: #f5f7ff;
}

.act-icon {
  font-size: 14px;
  line-height: 1;
}

.act-confirm {
  flex: 1;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 700;
  border: 0;
  border-radius: 8px;
  background: #5b6cf0;
  color: #fff;
  cursor: pointer;
  transition: background .15s, opacity .15s;
}

.act-confirm:hover:not(:disabled) {
  background: #4254d9;
}

.act-confirm:disabled {
  background: #e2e5eb;
  color: #b0b4bd;
  cursor: default;
}

.hidden-input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  pointer-events: none;
}
</style>
