<template>
  <div ref="mapContainer" class="map-container"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, provide } from 'vue'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import { useMapStore } from '@/stores'

const mapContainer = ref<HTMLDivElement | null>(null)
let map: mapboxgl.Map | null = null
const mapStore = useMapStore()
let syncTimer: number | null = null
let isApplyingStoreUpdate = false
let stopStoreWatch: (() => void) | null = null
const mapRef = ref<mapboxgl.Map | null>(null)
provide('mapInstance', mapRef)

onMounted(() => {
  if (!mapContainer.value) return

  // 设置 Mapbox access token
  mapboxgl.accessToken =
    'pk.eyJ1IjoiZGYweGV3YyIsImEiOiJjbTNoamh0NnMwZzZ6MnRwcXJkbWUxM2syIn0.eE5V7j0-uNb4WiwG2hXs0w'

  // 初始化地图，使用 store 中的初始值
  map = new mapboxgl.Map({
    container: mapContainer.value,
    style: 'mapbox://styles/mapbox/streets-v12',
    center: mapStore.center,
    zoom: mapStore.zoom,
    antialias: true,
  })
  mapRef.value = map

  // 添加导航控件（缩放和旋转）
  map.addControl(new mapboxgl.NavigationControl(), 'top-right')

  // 添加全屏控件
  map.addControl(new mapboxgl.FullscreenControl(), 'top-right')

  // 地图加载完成事件
  map.on('load', () => {
    console.log('地图加载完成')
  })

  // 地图错误处理
  map.on('error', (e) => {
    console.error('地图加载错误:', e)
  })

  // 监听地图移动，使用防抖降低频率，避免拖动/缩放卡顿
  map.on('move', () => {
    if (syncTimer) {
      clearTimeout(syncTimer)
    }
    syncTimer = window.setTimeout(() => {
      if (!map || isApplyingStoreUpdate) return
      const center = map.getCenter()
      mapStore.setCenter([center.lng, center.lat])
      mapStore.setZoom(map.getZoom())
      syncTimer = null
    }, 150)
  })

  // 监听 store 中心/缩放变化，驱动地图视图（防止循环用标记位）
  stopStoreWatch = watch(
    [() => mapStore.center, () => mapStore.zoom],
    ([targetCenter, targetZoom]) => {
      if (!map || !targetCenter || targetZoom === undefined) return
      const currentCenter = map.getCenter()
      const currentZoom = map.getZoom()
      const centerChanged = currentCenter.lng !== targetCenter[0] || currentCenter.lat !== targetCenter[1]
      const zoomChanged = currentZoom !== targetZoom
      if (!centerChanged && !zoomChanged) return
      isApplyingStoreUpdate = true
      map.jumpTo({
        center: targetCenter,
        zoom: targetZoom,
      })
      isApplyingStoreUpdate = false
    }
  )
})

onBeforeUnmount(() => {
  // 清理地图实例
  if (map) {
    map.remove()
    map = null
    mapRef.value = null
  }
  if (syncTimer) {
    clearTimeout(syncTimer)
    syncTimer = null
  }
  if (stopStoreWatch) {
    stopStoreWatch()
    stopStoreWatch = null
  }
})
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 100%;
  position: relative;
}
</style>

