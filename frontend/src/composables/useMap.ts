/**
 * 地图相关组合式函数
 */
import { ref, onMounted, onBeforeUnmount, watch, type Ref } from 'vue'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import { MAPBOX_CONFIG, MAP_CONFIG } from '@/config'
import { useMapStore } from '@/stores'

export function useMap(
  container: Ref<HTMLDivElement | null>,
  mapRef?: Ref<{ value: mapboxgl.Map | null }>
) {
  const map = ref<mapboxgl.Map | null>(null)
  const mapStore = useMapStore()
  let syncTimer: ReturnType<typeof setTimeout> | null = null
  let isApplyingStoreUpdate = false
  let stopStoreWatch: (() => void) | null = null

  /**
   * 初始化地图
   */
  const initMap = () => {
    if (!container.value) return

    mapboxgl.accessToken = MAPBOX_CONFIG.ACCESS_TOKEN

    map.value = new mapboxgl.Map({
      container: container.value,
      style: MAPBOX_CONFIG.DEFAULT_STYLE,
      center: mapStore.center,
      zoom: mapStore.zoom,
      antialias: true,
    })

    // 同步到 mapRef（供兄弟组件使用）
    if (mapRef) {
      mapRef.value = map.value
    }

    // 添加导航控件
    map.value.addControl(new mapboxgl.NavigationControl(), 'top-right')
    map.value.addControl(new mapboxgl.FullscreenControl(), 'top-right')

    // 地图加载完成事件
    map.value.on('load', () => {
      console.log('地图加载完成')
    })

    // 地图错误处理
    map.value.on('error', e => {
      console.error('地图加载错误:', e)
    })

    // 监听地图移动，同步到 store
    map.value.on('move', () => {
      if (syncTimer) {
        clearTimeout(syncTimer)
      }
      syncTimer = setTimeout(() => {
        if (!map.value || isApplyingStoreUpdate) return
        const center = map.value.getCenter()
        mapStore.setCenter([center.lng, center.lat])
        mapStore.setZoom(map.value.getZoom())
        syncTimer = null
      }, MAP_CONFIG.SYNC_DELAY)
    })

    // 监听 store 变化，同步到地图
    stopStoreWatch = watch(
      [() => mapStore.center, () => mapStore.zoom],
      ([targetCenter, targetZoom]) => {
        if (!map.value || !targetCenter || targetZoom === undefined) return
        const currentCenter = map.value.getCenter()
        const currentZoom = map.value.getZoom()
        const centerChanged =
          currentCenter.lng !== targetCenter[0] || currentCenter.lat !== targetCenter[1]
        const zoomChanged = currentZoom !== targetZoom
        if (!centerChanged && !zoomChanged) return
        isApplyingStoreUpdate = true
        map.value.jumpTo({
          center: targetCenter,
          zoom: targetZoom,
        })
        isApplyingStoreUpdate = false
      }
    )

    return map.value
  }

  /**
   * 清理资源
   */
  const cleanup = () => {
    if (map.value) {
      map.value.remove()
      map.value = null
    }
    if (mapRef) {
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
  }

  onMounted(() => {
    initMap()
  })

  onBeforeUnmount(() => {
    cleanup()
  })

  return {
    map,
    initMap,
    cleanup,
  }
}
