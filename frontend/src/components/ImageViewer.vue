<template>
  <Teleport to="body">
    <div class="image-viewer-overlay" @click.self="handleClose">
      <div class="image-viewer-container">
        <!-- 关闭按钮 -->
        <button class="viewer-close" @click="handleClose">
          <el-icon><Close /></el-icon>
        </button>

        <!-- 上一张按钮 -->
        <button
          v-if="images.length > 1"
          class="viewer-nav viewer-prev"
          @click="handlePrev"
          :disabled="currentIndex === 0"
        >
          <el-icon><ArrowLeft /></el-icon>
        </button>

        <!-- 下一张按钮 -->
        <button
          v-if="images.length > 1"
          class="viewer-nav viewer-next"
          @click="handleNext"
          :disabled="currentIndex === images.length - 1"
        >
          <el-icon><ArrowRight /></el-icon>
        </button>

        <!-- 图片容器 -->
        <div class="viewer-content">
          <div class="viewer-image-wrapper">
            <img
              :src="currentImage.url"
              :alt="currentImage.title || 'Image'"
              class="viewer-image"
              @load="handleImageLoad"
              @error="handleImageError"
            />
            <div v-if="isLoading" class="viewer-loading">
              <el-icon class="is-loading"><Loading /></el-icon>
            </div>
          </div>

          <!-- 图片信息 -->
          <div v-if="currentImage.title" class="viewer-info">
            <div class="viewer-title">{{ currentImage.title }}</div>
            <div class="viewer-counter">
              {{ currentIndex + 1 }} / {{ images.length }}
            </div>
          </div>
        </div>

        <!-- 缩略图导航（如果图片数量较多） -->
        <div v-if="images.length > 1 && images.length <= 10" class="viewer-thumbnails">
          <div
            v-for="(image, index) in images"
            :key="index"
            class="thumbnail-item"
            :class="{ active: index === currentIndex }"
            @click="goToImage(index)"
          >
            <img :src="image.thumbnail || image.url" :alt="`Thumbnail ${index + 1}`" />
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Close, ArrowLeft, ArrowRight, Loading } from '@element-plus/icons-vue'
import type { ImageResult } from '@/types/api'

interface Props {
  images: ImageResult[]
  currentIndex: number
}

interface Emits {
  (e: 'close'): void
  (e: 'prev'): void
  (e: 'next'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const isLoading = ref(true)

const currentImage = computed(() => props.images[props.currentIndex] || props.images[0])

const handleClose = () => {
  emit('close')
}

const handlePrev = () => {
  if (props.currentIndex > 0) {
    emit('prev')
  }
}

const handleNext = () => {
  if (props.currentIndex < props.images.length - 1) {
    emit('next')
  }
}

const goToImage = (index: number) => {
  if (index < props.currentIndex) {
    for (let i = props.currentIndex; i > index; i--) {
      emit('prev')
    }
  } else if (index > props.currentIndex) {
    for (let i = props.currentIndex; i < index; i++) {
      emit('next')
    }
  }
}

const handleImageLoad = () => {
  isLoading.value = false
}

const handleImageError = () => {
  isLoading.value = false
}

// 键盘导航
const handleKeydown = (e: KeyboardEvent) => {
  switch (e.key) {
    case 'Escape':
      handleClose()
      break
    case 'ArrowLeft':
      handlePrev()
      break
    case 'ArrowRight':
      handleNext()
      break
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  document.body.style.overflow = 'hidden' // 防止背景滚动
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  document.body.style.overflow = ''
})
</script>

<style scoped>
.image-viewer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.2s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.image-viewer-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px 20px;
}

.viewer-close {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 40px;
  height: 40px;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  transition: all 0.2s;
  z-index: 10001;
}

.viewer-close:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.1);
}

.viewer-nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 50px;
  height: 50px;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  transition: all 0.2s;
  z-index: 10001;
}

.viewer-nav:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-50%) scale(1.1);
}

.viewer-nav:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.viewer-prev {
  left: 20px;
}

.viewer-next {
  right: 20px;
}

.viewer-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  max-width: 90vw;
  max-height: 80vh;
}

.viewer-image-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
}

.viewer-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 4px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}

.viewer-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #fff;
  font-size: 32px;
}

.viewer-info {
  margin-top: 20px;
  text-align: center;
  color: #fff;
  max-width: 80%;
}

.viewer-title {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
  word-break: break-word;
}

.viewer-counter {
  font-size: 14px;
  opacity: 0.8;
}

.viewer-thumbnails {
  display: flex;
  gap: 8px;
  padding: 20px;
  overflow-x: auto;
  max-width: 100%;
  justify-content: center;
}

.thumbnail-item {
  width: 60px;
  height: 60px;
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
  flex-shrink: 0;
}

.thumbnail-item:hover {
  border-color: rgba(255, 255, 255, 0.5);
  transform: scale(1.1);
}

.thumbnail-item.active {
  border-color: #409eff;
}

.thumbnail-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 响应式 */
@media (max-width: 768px) {
  .viewer-nav {
    width: 40px;
    height: 40px;
    font-size: 20px;
  }

  .viewer-prev {
    left: 10px;
  }

  .viewer-next {
    right: 10px;
  }

  .viewer-thumbnails {
    padding: 10px;
  }

  .thumbnail-item {
    width: 50px;
    height: 50px;
  }
}
</style>
