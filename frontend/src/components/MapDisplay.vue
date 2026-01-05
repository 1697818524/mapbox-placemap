<template>
  <div ref="mapContainer" class="map-container"></div>
</template>

<script setup lang="ts">
import { ref, inject, watch } from 'vue'
import type mapboxgl from 'mapbox-gl'
import { useMap } from '@/composables'

const mapContainer = ref<HTMLDivElement | null>(null)

// 从父组件注入 mapRef
type MapRef = { value: mapboxgl.Map | null }
const injected = inject<MapRef>('mapInstance')
if (!injected) {
  throw new Error('mapInstance not provided')
}
const mapRef = injected

// 使用地图组合式函数，传入 mapRef 用于同步
const { map } = useMap(mapContainer, mapRef)

// 将地图实例保存到 mapRef（供兄弟组件使用）
watch(
  map,
  newMap => {
    if (newMap) {
      mapRef.value = newMap
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 100%;
  position: relative;
}
</style>
