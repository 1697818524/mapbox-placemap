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
  height: 100%;
}
.navbar {
  height: 88px;
  background-color: #fff;
  flex-shrink: 0;
  border-bottom: 1px solid #e7eaf0;
}
.main-content {
  display: flex;
  flex-grow: 1;
  background-color: #f4f6f8;
  flex-direction: row;
  overflow: hidden;
  min-height: 0;
}
.left-sidebar {
  width: 316px;
  background-color: #fff;
  flex-shrink: 0;
  border-right: 1px solid #e4e7ed;
}
.map-container {
  flex-grow: 1;
  background-color: #edf1f5;
  flex-shrink: 0;
  min-width: 0;
}
.right-sidebar {
  width: 392px;
  background-color: #fff;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
  border-left: 1px solid #e4e7ed;
}
.right-sidebar :deep(.map-style) {
  flex: 1;
  min-height: 0;
}
</style>
