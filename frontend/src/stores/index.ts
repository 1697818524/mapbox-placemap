import { defineStore } from 'pinia'
import { ref } from 'vue'
import i18n from '@/i18n'
import { storage } from '@/utils'
import { MAP_CONFIG, STORAGE_KEYS } from '@/config'
import { type MapState, type LngLatTuple } from '@/types/map'

/** 后端 SchemeScores 与配色方案绑定时的指标（GA 方案含 harmony / place_representativeness） */
export interface SchemeScores {
  semantic_fit?: number
  readability?: number
  diversity?: number
  harmony?: number | null
  place_representativeness?: number | null
}

export interface ColorSchemeItem {
  /** Mapbox 图层 id，不参与算法数值计算，仅关联样式图层 */
  id: string
  /** HEX 颜色 */
  color: string
  /** 占比（权重） */
  weight: number
  /**
   * 粗语义类型，与分割流水线五类一致（architecture | roadnet | green | landmark | water）
   * 旧数据或未知图层可省略
   */
  semantic?: string
}

export interface ColorScheme {
  layers: ColorSchemeItem[]
}

// 带 ID 的颜色方案（用于生成的方案）
export interface ColorSchemeWithId extends ColorScheme {
  id: string
  scores?: SchemeScores | null
}

export const useAppStore = defineStore('app', () => {
  const locale = ref<string>(storage.get<string>(STORAGE_KEYS.LOCALE, 'zh-CN') || 'zh-CN')

  const setLocale = (lang: 'zh-CN' | 'en-US') => {
    locale.value = lang
    i18n.global.locale.value = lang
    storage.set(STORAGE_KEYS.LOCALE, lang)
    document.documentElement.lang = lang
  }

  return {
    locale,
    setLocale,
  }
})

export const useMapStore = defineStore('map', () => {
  const center = ref<MapState['center']>(MAP_CONFIG.DEFAULT_CENTER)
  const zoom = ref<MapState['zoom']>(MAP_CONFIG.DEFAULT_ZOOM)

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

  // 颜色方案列表（用于遗传算法，支持带 id 的方案）
  const colorSchemes = ref<Array<ColorScheme | ColorSchemeWithId>>([])

  /** 画廊中选中的方案下标（与 colorSchemes 对齐） */
  const selectedSchemeIndex = ref(0)

  /** 最近一次 pipeline 任务 id（用于 /api/schemes/generate 附带 job_id） */
  const lastPipelineJobId = ref<string | null>(null)

  /** 流水线已成功且具备调色板候选（enable_cluster 时需 palette_*.csv），才允许「生成方案」 */
  const schemeGenerationReady = ref(false)

  /** 将 store 中的当前样式同步为 colorSchemes[selectedSchemeIndex]（不改变列表） */
  const syncCurrentSchemeFromGalleryIndex = () => {
    const list = colorSchemes.value
    if (!list.length) {
      currentScheme.value = { layers: [] }
      return
    }
    const i = Math.min(Math.max(0, selectedSchemeIndex.value), list.length - 1)
    selectedSchemeIndex.value = i
    const raw = list[i]
    currentScheme.value = {
      layers: raw.layers.map(l => ({
        id: l.id,
        color: l.color,
        weight: l.weight ?? 1,
        semantic: l.semantic,
      })),
    }
  }

  const setSelectedSchemeIndex = (index: number) => {
    if (!colorSchemes.value.length) {
      selectedSchemeIndex.value = 0
      return
    }
    selectedSchemeIndex.value = Math.min(Math.max(0, index), colorSchemes.value.length - 1)
    syncCurrentSchemeFromGalleryIndex()
  }

  // 设置当前颜色方案
  const setCurrentScheme = (scheme: ColorScheme) => {
    currentScheme.value = scheme
  }

  // 添加颜色方案到列表
  const addColorScheme = (scheme: ColorScheme | ColorSchemeWithId) => {
    colorSchemes.value.push(scheme)
  }

  // 设置颜色方案列表
  const setColorSchemes = (schemes: Array<ColorScheme | ColorSchemeWithId>) => {
    colorSchemes.value = schemes
    selectedSchemeIndex.value = 0
    syncCurrentSchemeFromGalleryIndex()
  }

  // 清空颜色方案列表
  const clearColorSchemes = () => {
    colorSchemes.value = []
    selectedSchemeIndex.value = 0
    currentScheme.value = { layers: [] }
  }

  const setLastPipelineJobId = (id: string | null) => {
    lastPipelineJobId.value = id
    if (!id) {
      schemeGenerationReady.value = false
    }
  }

  const setSchemeGenerationReady = (ready: boolean) => {
    schemeGenerationReady.value = ready
  }

  return {
    currentScheme,
    colorSchemes,
    selectedSchemeIndex,
    lastPipelineJobId,
    schemeGenerationReady,
    setCurrentScheme,
    addColorScheme,
    setColorSchemes,
    clearColorSchemes,
    setLastPipelineJobId,
    setSchemeGenerationReady,
    setSelectedSchemeIndex,
    syncCurrentSchemeFromGalleryIndex,
  }
})
