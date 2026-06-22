/** *
首页：左侧勾选/上传图片并点击「构建样本集」，中间地图展示，右侧调整初始配色并可在此触发「生成方案」跳转至方案页。
*/
<template>
  <div class="container">
    <div class="navbar">
      <Navbar />
    </div>
    <div class="main-content">
      <div class="left-sidebar">
        <MapInfo />
      </div>
      <div class="map-container">
        <MapDisplay />
      </div>
      <div class="right-sidebar">
        <MapStyle footer-mode="generate" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, provide } from 'vue'
import Navbar from '@/components/Navbar.vue'
import MapInfo from '@/components/MapInfo.vue'
import MapDisplay from '@/components/MapDisplay.vue'
import MapStyle from '@/components/MapStyle.vue'
import type { MapboxMapInstance } from '@/composables'

const mapInstanceRef = ref<MapboxMapInstance | null>(null)
provide('mapInstance', mapInstanceRef)
</script>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  min-height: 0;
  overflow: hidden;
  background: #eef1f5;
}
.navbar {
  height: 64px;
  background-color: #fff;
  flex-shrink: 0;
  border-bottom: 1px solid #dfe4eb;
  position: relative;
  z-index: 10;
}
.main-content {
  display: grid;
  grid-template-columns: 336px minmax(0, 1fr) 368px;
  grid-template-rows: minmax(0, 1fr);
  flex: 1 1 0;
  height: calc(100vh - 64px);
  background-color: #eef1f5;
  overflow: hidden;
  min-height: 0;
}
.left-sidebar {
  background-color: #fff;
  min-width: 0;
  min-height: 0;
  height: 100%;
  overflow: hidden;
  border-right: 1px solid #dfe4eb;
}
.map-container {
  position: relative;
  background-color: #e8edf2;
  min-width: 0;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}
.right-sidebar {
  background-color: #fff;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  height: 100%;
  overflow: hidden;
  border-left: 1px solid #dfe4eb;
}
.left-sidebar :deep(.map-info),
.right-sidebar :deep(.map-style) {
  width: 100%;
  height: 100%;
  min-height: 0;
}

@media (max-width: 1440px) {
  .main-content {
    grid-template-columns: 306px minmax(0, 1fr) 344px;
  }
}

@media (max-width: 1120px) {
  .main-content {
    grid-template-columns: 288px minmax(0, 1fr) 320px;
  }
}
</style>
