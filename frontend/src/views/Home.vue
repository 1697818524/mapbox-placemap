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
import type mapboxgl from 'mapbox-gl'

const mapInstanceRef = ref<mapboxgl.Map | null>(null)
provide('mapInstance', mapInstanceRef)
</script>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.navbar {
  height: 100px;
  background-color: #fefefe;
  flex-shrink: 0;
}
.main-content {
  display: flex;
  flex-grow: 1;
  background-color: #e0cece;
  flex-direction: row;
  overflow: hidden;
  min-height: 0;
}
.left-sidebar {
  width: 300px;
  background-color: aqua;
  flex-shrink: 0;
}
.map-container {
  flex-grow: 1;
  background-color: #eec9c9;
  flex-shrink: 0;
  min-width: 0;
}
.right-sidebar {
  width: 400px;
  background-color: #f0f0f0;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.right-sidebar :deep(.map-style) {
  flex: 1;
  min-height: 0;
}
</style>
