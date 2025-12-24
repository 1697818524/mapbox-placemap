<template>
  <div class="map-style">
    <!-- 在这里重写你的样式控制代码 -->
  </div>
</template>

<script setup lang="ts">
import { inject } from 'vue'
import type mapboxgl from 'mapbox-gl'

type MapRef = { value: mapboxgl.Map | null }

const injected = inject<MapRef>('mapInstance', { value: null })
const mapRef = injected

// 获取地图实例的辅助函数
const getMap = () => mapRef?.value ?? null
</script>

<style scoped>
.map-style {
  height: 100%;
  overflow-y: auto;
  padding: 12px;
  background: #fff;
}
</style>
