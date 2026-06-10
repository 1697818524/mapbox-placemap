<template>
  <div ref="mapContainer" class="map-container"></div>
</template>

<script setup lang="ts">
import { ref, inject, type Ref } from 'vue'
import { useMap, type MapboxMapInstance } from '@/composables'

const mapContainer = ref<HTMLDivElement | null>(null)

// 与 Home.vue provide 对齐：Ref<Map | null>
const mapInstanceRef = inject<Ref<MapboxMapInstance | null>>('mapInstance')
if (!mapInstanceRef) {
  throw new Error('mapInstance not provided')
}

useMap(mapContainer, mapInstanceRef)
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 100%;
  position: relative;
}
</style>
