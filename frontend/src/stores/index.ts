import { defineStore } from 'pinia'
import { ref } from 'vue'
import i18n from '@/i18n'
import { type MapState, type LngLatTuple } from '@/types/map'

export const useAppStore = defineStore('app', () => {
  const locale = ref<string>(localStorage.getItem('locale') || 'zh-CN')

  const setLocale = (lang: 'zh-CN' | 'en-US') => {
    locale.value = lang
    i18n.global.locale.value = lang
    localStorage.setItem('locale', lang)
    document.documentElement.lang = lang
  }

  return {
    locale,
    setLocale,
  }
})

export const useMapStore = defineStore('map', () => {
  const center = ref<MapState['center']>([116.3974, 39.9093]) // 默认中心点：北京天安门
  const zoom = ref<MapState['zoom']>(10)

  const setCenter = (newCenter: LngLatTuple) => {
    center.value = newCenter
  }

  const setZoom = (newZoom: number) => {
    zoom.value = newZoom
  }

  const setView = (newCenter: LngLatTuple, newZoom?: number) => {
    center.value = newCenter
    if (newZoom !== undefined) {
      zoom.value = newZoom
    }
  }

  return {
    center,
    zoom,
    setCenter,
    setZoom,
    setView,
  }
})

