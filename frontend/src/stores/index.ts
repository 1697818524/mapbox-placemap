import { defineStore } from 'pinia'
import { ref } from 'vue'
import i18n from '@/i18n'
import { type MapState, type LngLatTuple } from '@/types/map'

// 颜色方案类型定义
export interface ColorSchemeItem {
  id: string  // 图层ID
  color: string  // hex颜色值，如 "#FF0000"
  weight: number  // 占比（权重），默认等权重
}

export interface ColorScheme {
  layers: ColorSchemeItem[]
}

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

// 颜色方案 Store
export const useColorSchemeStore = defineStore('colorScheme', () => {
  // 当前颜色方案
  const currentScheme = ref<ColorScheme>({ layers: [] })
  
  // 颜色方案列表（用于遗传算法）
  const colorSchemes = ref<ColorScheme[]>([])

  // 设置当前颜色方案
  const setCurrentScheme = (scheme: ColorScheme) => {
    currentScheme.value = scheme
  }

  // 添加颜色方案到列表
  const addColorScheme = (scheme: ColorScheme) => {
    colorSchemes.value.push(scheme)
  }

  // 设置颜色方案列表
  const setColorSchemes = (schemes: ColorScheme[]) => {
    colorSchemes.value = schemes
  }

  // 清空颜色方案列表
  const clearColorSchemes = () => {
    colorSchemes.value = []
  }

  return {
    currentScheme,
    colorSchemes,
    setCurrentScheme,
    addColorScheme,
    setColorSchemes,
    clearColorSchemes,
  }
})

