<template>
  <div class="map-style">
    <div class="style-header">
      <h3>{{ t('mapStyle.title') }}</h3>
      <div class="header-actions">
        <el-button size="small" @click="resetAllColors">{{ t('mapStyle.resetAll') }}</el-button>
      </div>
    </div>

    <el-scrollbar class="style-content">
      <el-collapse v-model="activeCategories" class="category-section studio-collapse">
        <!-- 水体（图层 id 与样式一致，未改列表） -->
        <el-collapse-item name="water" :title="t('mapStyle.water')">
          <div class="layer-list">
            <div v-for="layer in waterLayers" :key="layer.id" class="studio-layer-row">
              <div class="studio-layer-main">
                <div class="studio-layer-title-row">
                  <span class="studio-layer-name">{{ getLayerName(layer.nameKey) }}</span>
                  <span class="studio-paint-key">{{ layer.paintProperty }}</span>
                </div>
                <div class="studio-layer-id">{{ layer.id }}</div>
                <div class="studio-layer-meta">
                  <span class="studio-hex">{{ layerHexLine(layer) }}</span>
                  <template v-if="layerSemanticLine(layer)">
                    <span class="studio-meta-sep">·</span>
                    <span>{{ layerSemanticLine(layer) }}</span>
                  </template>
                </div>
              </div>
              <div class="studio-color-actions">
                <el-color-picker
                  v-model="layerColors[layer.id]"
                  :predefine="predefineColors"
                  size="small"
                  @change="color => updateLayerColor(layer.id, color, layer.paintProperty)"
                />
                <el-button
                  size="small"
                  text
                  class="studio-reset-btn"
                  @click="resetLayerColor(layer.id, layer.defaultColor, layer.paintProperty)"
                >
                  {{ t('mapStyle.reset') }}
                </el-button>
              </div>
            </div>
          </div>
        </el-collapse-item>

        <el-collapse-item name="roads" :title="t('mapStyle.roads')">
          <div class="layer-list">
            <div v-for="layer in roadLayers" :key="layer.id" class="studio-layer-row">
              <div class="studio-layer-main">
                <div class="studio-layer-title-row">
                  <span class="studio-layer-name">{{ getLayerName(layer.nameKey) }}</span>
                  <span class="studio-paint-key">{{ layer.paintProperty }}</span>
                </div>
                <div class="studio-layer-id">{{ layer.id }}</div>
                <div class="studio-layer-meta">
                  <span class="studio-hex">{{ layerHexLine(layer) }}</span>
                  <template v-if="layerSemanticLine(layer)">
                    <span class="studio-meta-sep">·</span>
                    <span>{{ layerSemanticLine(layer) }}</span>
                  </template>
                </div>
              </div>
              <div class="studio-color-actions">
                <el-color-picker
                  v-model="layerColors[layer.id]"
                  :predefine="predefineColors"
                  size="small"
                  @change="color => updateLayerColor(layer.id, color, layer.paintProperty)"
                />
                <el-button
                  size="small"
                  text
                  class="studio-reset-btn"
                  @click="resetLayerColor(layer.id, layer.defaultColor, layer.paintProperty)"
                >
                  {{ t('mapStyle.reset') }}
                </el-button>
              </div>
            </div>
          </div>
        </el-collapse-item>

        <el-collapse-item name="buildings" :title="t('mapStyle.buildings')">
          <div class="layer-list">
            <div v-for="layer in buildingLayers" :key="layer.id" class="studio-layer-row">
              <div class="studio-layer-main">
                <div class="studio-layer-title-row">
                  <span class="studio-layer-name">{{ getLayerName(layer.nameKey) }}</span>
                  <span class="studio-paint-key">{{ layer.paintProperty }}</span>
                </div>
                <div class="studio-layer-id">{{ layer.id }}</div>
                <div class="studio-layer-meta">
                  <span class="studio-hex">{{ layerHexLine(layer) }}</span>
                  <template v-if="layerSemanticLine(layer)">
                    <span class="studio-meta-sep">·</span>
                    <span>{{ layerSemanticLine(layer) }}</span>
                  </template>
                </div>
              </div>
              <div class="studio-color-actions">
                <el-color-picker
                  v-model="layerColors[layer.id]"
                  :predefine="predefineColors"
                  size="small"
                  @change="color => updateLayerColor(layer.id, color, layer.paintProperty)"
                />
                <el-button
                  size="small"
                  text
                  class="studio-reset-btn"
                  @click="resetLayerColor(layer.id, layer.defaultColor, layer.paintProperty)"
                >
                  {{ t('mapStyle.reset') }}
                </el-button>
              </div>
            </div>
          </div>
        </el-collapse-item>

        <el-collapse-item name="green" :title="t('mapStyle.green')">
          <div class="layer-list">
            <div v-for="layer in greenLayers" :key="layer.id" class="studio-layer-row">
              <div class="studio-layer-main">
                <div class="studio-layer-title-row">
                  <span class="studio-layer-name">{{ getLayerName(layer.nameKey) }}</span>
                  <span class="studio-paint-key">{{ layer.paintProperty }}</span>
                </div>
                <div class="studio-layer-id">{{ layer.id }}</div>
                <div class="studio-layer-meta">
                  <span class="studio-hex">{{ layerHexLine(layer) }}</span>
                  <template v-if="layerSemanticLine(layer)">
                    <span class="studio-meta-sep">·</span>
                    <span>{{ layerSemanticLine(layer) }}</span>
                  </template>
                </div>
              </div>
              <div class="studio-color-actions">
                <el-color-picker
                  v-model="layerColors[layer.id]"
                  :predefine="predefineColors"
                  size="small"
                  @change="color => updateLayerColor(layer.id, color, layer.paintProperty)"
                />
                <el-button
                  size="small"
                  text
                  class="studio-reset-btn"
                  @click="resetLayerColor(layer.id, layer.defaultColor, layer.paintProperty)"
                >
                  {{ t('mapStyle.reset') }}
                </el-button>
              </div>
            </div>
          </div>
        </el-collapse-item>

        <el-collapse-item name="labels" :title="t('mapStyle.labels')">
          <div class="layer-list">
            <div v-for="layer in labelLayers" :key="layer.id" class="studio-layer-row">
              <div class="studio-layer-main">
                <div class="studio-layer-title-row">
                  <span class="studio-layer-name">{{ getLayerName(layer.nameKey) }}</span>
                  <span class="studio-paint-key">{{ layer.paintProperty }}</span>
                </div>
                <div class="studio-layer-id">{{ layer.id }}</div>
                <div class="studio-layer-meta">
                  <span class="studio-hex">{{ layerHexLine(layer) }}</span>
                  <template v-if="layerSemanticLine(layer)">
                    <span class="studio-meta-sep">·</span>
                    <span>{{ layerSemanticLine(layer) }}</span>
                  </template>
                </div>
              </div>
              <div class="studio-color-actions">
                <el-color-picker
                  v-model="layerColors[layer.id]"
                  :predefine="predefineColors"
                  size="small"
                  @change="color => updateLayerColor(layer.id, color, layer.paintProperty)"
                />
                <el-button
                  size="small"
                  text
                  class="studio-reset-btn"
                  @click="resetLayerColor(layer.id, layer.defaultColor, layer.paintProperty)"
                >
                  {{ t('mapStyle.reset') }}
                </el-button>
              </div>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-scrollbar>

    <!-- 首页：生成多套方案并跳转工作室 -->
    <div v-if="footerMode === 'generate'" class="generate-section">
      <el-tooltip :content="generateBlockedReason" placement="top" :disabled="canGenerate">
        <span class="generate-btn-wrap">
          <el-button
            type="primary"
            :loading="isGenerating"
            :disabled="!canGenerate"
            class="generate-button"
            @click="handleGenerateSchemes"
          >
            <el-icon v-if="!isGenerating"><MagicStick /></el-icon>
            {{ isGenerating ? t('mapStyle.generating') : t('mapStyle.generateSchemes') }}
          </el-button>
        </span>
      </el-tooltip>
    </div>

    <!-- 方案页：左右切换候选方案 -->
    <div v-else class="generate-section gallery-footer">
      <template v-if="colorSchemes.length === 0">
        <p class="gallery-hint">{{ t('mapStyle.galleryEmpty') }}</p>
      </template>
      <template v-else>
        <div class="gallery-row">
          <el-button
            size="small"
            class="gallery-btn"
            :disabled="!canGalleryPrev"
            @click="galleryPrev"
          >
            {{ t('generatePage.prevScheme') }}
          </el-button>
          <span class="gallery-counter">{{ galleryCounter }}</span>
          <el-button
            size="small"
            class="gallery-btn"
            :disabled="!canGalleryNext"
            @click="galleryNext"
          >
            {{ t('generatePage.nextScheme') }}
          </el-button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted, inject, computed, type Ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { MagicStick } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { storeToRefs } from 'pinia'
import type mapboxgl from 'mapbox-gl'
import { semanticForLayerId } from '@/config/placemapSemantics'
import {
  waterLayers,
  roadLayers,
  buildingLayers,
  greenLayers,
  labelLayers,
  getAllConfigurableLayers,
  type LayerConfig,
} from '@/config/mapStyleLayers'
import { useColorSchemeStore, type ColorScheme, type ColorSchemeItem } from '@/stores'
import { schemeApi } from '@/api/scheme'

const props = withDefaults(
  defineProps<{
    /** generate：首页调用接口并跳转 /generate；gallery：仅上一/下一方案 */
    footerMode?: 'generate' | 'gallery'
  }>(),
  { footerMode: 'generate' },
)

const { t } = useI18n()
const router = useRouter()

const mapInstanceRef = inject<Ref<mapboxgl.Map | null>>('mapInstance')
if (!mapInstanceRef) {
  throw new Error('mapInstance not provided')
}

// Pinia store
const colorSchemeStore = useColorSchemeStore()
const { colorSchemes, selectedSchemeIndex, schemeGenerationReady } = storeToRefs(colorSchemeStore)

const getMap = (): mapboxgl.Map | null => mapInstanceRef.value

const canGalleryPrev = computed(
  () => colorSchemes.value.length > 0 && selectedSchemeIndex.value > 0,
)
const canGalleryNext = computed(
  () =>
    colorSchemes.value.length > 0 &&
    selectedSchemeIndex.value < colorSchemes.value.length - 1,
)
const galleryCounter = computed(() => {
  const n = colorSchemes.value.length
  if (!n) return ''
  return t('generatePage.schemeCounter', {
    current: selectedSchemeIndex.value + 1,
    total: n,
  })
})

function galleryPrev() {
  colorSchemeStore.setSelectedSchemeIndex(selectedSchemeIndex.value - 1)
}
function galleryNext() {
  colorSchemeStore.setSelectedSchemeIndex(selectedSchemeIndex.value + 1)
}

const isGenerating = ref(false)
const canGenerate = computed(
  () =>
    props.footerMode === 'generate' &&
    colorSchemeStore.currentScheme.layers.length > 0 &&
    schemeGenerationReady.value,
)

const generateBlockedReason = computed(() => {
  if (props.footerMode !== 'generate') return ''
  if (colorSchemeStore.currentScheme.layers.length === 0) return t('mapStyle.noCurrentScheme')
  if (!schemeGenerationReady.value) return t('mapStyle.generateBlockedNeedPipeline')
  return ''
})

async function handleGenerateSchemes() {
  const currentScheme = colorSchemeStore.currentScheme
  if (!currentScheme.layers.length) {
    ElMessage.warning(t('mapStyle.noCurrentScheme'))
    return
  }
  if (!schemeGenerationReady.value) {
    ElMessage.warning(t('mapStyle.generateBlockedNeedPipeline'))
    return
  }

  isGenerating.value = true
  try {
    const response = await schemeApi.generateSchemes({
      currentScheme,
      count: 5,
      jobId: colorSchemeStore.lastPipelineJobId || undefined,
    })
    colorSchemeStore.setColorSchemes(response.schemes)
    ElMessage.success(t('mapStyle.generateSuccess', { count: response.schemes.length }))
    await router.push('/generate')
  } catch (error) {
    console.error('生成方案失败:', error)
    ElMessage.error(
      error instanceof Error ? error.message : t('mapStyle.generateError'),
    )
  } finally {
    isGenerating.value = false
  }
}

// 展开的类别
const activeCategories = ref<string[]>(['water', 'roads', 'buildings', 'green', 'labels'])

// 图层颜色状态（保存用户设置的颜色）
const layerColors = reactive<Record<string, string>>({})

// 保存原始默认颜色（从地图样式获取）
const originalColors = reactive<Record<string, string>>({})

// 保存当前地图的 center 和 zoom
const currentCenter = ref<[number, number] | null>(null)
const currentZoom = ref<number | null>(null)

// 预定义颜色
const predefineColors = [
  '#FF4444',
  '#FF8800',
  '#FFBB00',
  '#88DD00',
  '#00DD88',
  '#00DDFF',
  '#0088FF',
  '#4400FF',
  '#8800FF',
  '#FF00FF',
  '#FF0088',
  '#FFFFFF',
  '#000000',
  '#888888',
]

const getLayerName = (nameKey: string): string => {
  return t(`mapStyle.layers.${nameKey}`)
}

const listAllLayers = () => {
  const map = getMap()
  if (!map) {
    return
  }

  if (!map.isStyleLoaded()) {
    map.once('styledata', () => {
      setTimeout(() => listAllLayers(), 500)
    })
    return
  }

  try {
    const style = map.getStyle()

    if (typeof style === 'string') {
      return
    }

    const layers = style.layers || []
  } catch (e) {
    console.error('列出图层失败:', e)
  }
}

// 监听地图实例，保存 center 和 zoom
watch(
  () => mapInstanceRef.value,
  mapInstance => {
    if (
      !mapInstance ||
      typeof mapInstance.on !== 'function' ||
      typeof mapInstance.getCenter !== 'function' ||
      typeof mapInstance.getZoom !== 'function'
    ) {
      return
    }

    const updatePosition = () => {
      const center = mapInstance.getCenter()
      currentCenter.value = [center.lng, center.lat]
      currentZoom.value = mapInstance.getZoom()
    }

    mapInstance.on('moveend', updatePosition)
    mapInstance.on('zoomend', updatePosition)

    const initMap = () => {
      updatePosition()

      setTimeout(() => {
        updateColorSchemeInStore()
      }, 500)

      const tryListLayers = () => {
        if (mapInstance.isStyleLoaded()) {
          listAllLayers()
        } else {
          mapInstance.once('load', () => {
            setTimeout(() => {
              listAllLayers()
            }, 1000)
          })
        }
      }

      tryListLayers()
      setTimeout(() => {
        tryListLayers()
      }, 2000)
      setTimeout(() => {
        tryListLayers()
      }, 5000)
    }

    if (typeof mapInstance.isStyleLoaded === 'function' && mapInstance.isStyleLoaded()) {
      initMap()
      setTimeout(() => saveOriginalColors(), 500)
    } else if (typeof mapInstance.once === 'function') {
      mapInstance.once('load', () => {
        initMap()
        setTimeout(() => saveOriginalColors(), 500)
      })
    }
  },
  { immediate: true },
)

// 保存原始颜色值（在地图加载时，保存所有可配置图层的默认颜色）
const saveOriginalColors = () => {
  const map = getMap()
  if (!map || !map.isStyleLoaded()) {
    return
  }

  try {
    const allLayersConfig = [
      ...waterLayers,
      ...roadLayers,
      ...buildingLayers,
      ...greenLayers,
      ...labelLayers,
    ]

    let savedCount = 0
    let skippedCount = 0

    allLayersConfig.forEach(layerConfig => {
      const layerId = layerConfig.id

      // 检查图层是否存在
      if (!map.getLayer(layerId)) {
        skippedCount++
        return
      }

      try {
        // 获取当前颜色值（这是 Mapbox 的默认值，因为此时用户还没有修改）
        const currentColor = map.getPaintProperty(layerId, layerConfig.paintProperty)
        if (currentColor && typeof currentColor === 'string') {
          // 保存原始颜色（如果还没有保存过）
          if (!originalColors[layerId]) {
            originalColors[layerId] = currentColor
            savedCount++
          }
        } else {
          skippedCount++
        }
      } catch (error) {
        skippedCount++
      }
    })
  } catch (error) {
    // 静默处理错误
  }
}

// 应用颜色到地图（使用高性能的 setPaintProperty API）
const applyColorsToMap = () => {
  const map = getMap()
  if (!map) {
    return
  }

  // 检查样式是否已加载
  if (!map.isStyleLoaded()) {
    map.once('load', () => {
      setTimeout(() => applyColorsToMap(), 100)
    })
    return
  }

  try {
    // 合并所有图层配置
    const allLayersConfig = [
      ...waterLayers,
      ...roadLayers,
      ...buildingLayers,
      ...greenLayers,
      ...labelLayers,
    ]

    let modifiedCount = 0

    // 应用所有已设置的颜色（使用 setPaintProperty，性能更好）
    Object.keys(layerColors).forEach(layerId => {
      const color = layerColors[layerId]
      if (!color) return

      // 找到对应的图层配置
      const layerConfig = allLayersConfig.find(l => l.id === layerId)
      if (!layerConfig) {
        return
      }

      // 检查图层是否存在
      if (!map.getLayer(layerId)) {
        return
      }

      // 转换颜色格式
      const mapboxColor = hexToRgb(color)

      try {
        // 使用 setPaintProperty 直接更新颜色（高性能，不会重新加载整个样式）
        map.setPaintProperty(layerId, layerConfig.paintProperty, mapboxColor)
        modifiedCount++
      } catch (error) {
        // 静默处理错误
      }
    })
  } catch (error) {
    console.error('应用颜色失败:', error)
  }
}

// 重置图层颜色为默认值（恢复原始颜色）
const resetLayerColorToDefault = (layerId: string, paintProperty: string) => {
  const map = getMap()
  if (!map || !map.isStyleLoaded()) {
    return
  }

  try {
    // 检查图层是否存在
    if (!map.getLayer(layerId)) {
      return
    }

    // 获取保存的原始颜色
    const originalColor = originalColors[layerId]
    if (originalColor) {
      // 恢复原始颜色
      map.setPaintProperty(layerId, paintProperty, originalColor)
    } else {
      // 如果没有保存的原始颜色，尝试从当前样式获取
      const currentColor = map.getPaintProperty(layerId, paintProperty)
      if (currentColor && typeof currentColor === 'string') {
        // 保存为原始颜色并保持当前值（可能是默认值）
        originalColors[layerId] = currentColor
      }
    }
  } catch (error) {
    // 静默处理错误
  }
}

// 更新图层颜色
const updateLayerColor = (layerId: string, color: string | null, paintProperty: string) => {
  const map = getMap()
  if (!map) {
    return
  }

  if (!color) {
    // 如果颜色为空，删除该图层的颜色设置
    delete layerColors[layerId]
    // 更新 Pinia store
    updateColorSchemeInStore()
    // 重置图层颜色为默认值
    const layerConfig = [
      ...waterLayers,
      ...roadLayers,
      ...buildingLayers,
      ...greenLayers,
      ...labelLayers,
    ].find(l => l.id === layerId)
    if (layerConfig) {
      resetLayerColorToDefault(layerId, layerConfig.paintProperty)
    }
    return
  }

  // 保存颜色状态
  layerColors[layerId] = color

  // 更新 Pinia store
  updateColorSchemeInStore()

  // 应用颜色到地图（高性能方法）
  applyColorsToMap()
}

// 重置单个图层颜色
const resetLayerColor = (
  layerId: string,
  defaultColor: string | undefined,
  paintProperty: string
) => {
  // 删除该图层的颜色设置
  delete layerColors[layerId]

  // 更新 Pinia store
  updateColorSchemeInStore()

  // 重置图层颜色为默认值
  resetLayerColorToDefault(layerId, paintProperty)
}

// 重置所有颜色
const resetAllColors = () => {
  // 获取所有图层配置
  const allLayersConfig = [
    ...waterLayers,
    ...roadLayers,
    ...buildingLayers,
    ...greenLayers,
    ...labelLayers,
  ]

  // 重置每个图层的颜色
  allLayersConfig.forEach(layerConfig => {
    if (layerColors[layerConfig.id]) {
      resetLayerColorToDefault(layerConfig.id, layerConfig.paintProperty)
    }
  })

  // 清空所有颜色设置
  Object.keys(layerColors).forEach(key => {
    delete layerColors[key]
  })

  // 更新 Pinia store
  updateColorSchemeInStore()
}

// 将十六进制颜色转换为 RGB 格式（Mapbox 需要的格式）
const hexToRgb = (hex: string): string => {
  // 如果是 rgba 格式，直接返回
  if (hex.startsWith('rgba') || hex.startsWith('rgb')) {
    return hex
  }

  // 移除 # 号
  const cleanHex = hex.replace('#', '')

  // 解析 RGB
  const r = parseInt(cleanHex.substring(0, 2), 16)
  const g = parseInt(cleanHex.substring(2, 4), 16)
  const b = parseInt(cleanHex.substring(4, 6), 16)

  return `rgb(${r}, ${g}, ${b})`
}

// 从地图样式中获取图层的默认颜色
const getDefaultColorFromMap = (layerId: string, paintProperty: string): string | null => {
  const map = getMap()
  if (!map || !map.isStyleLoaded()) {
    return null
  }

  try {
    // 检查图层是否存在
    if (!map.getLayer(layerId)) {
      return null
    }

    // 使用 Mapbox API 获取当前计算后的颜色值
    // getPaintProperty 会返回计算后的值（对于表达式会计算，对于静态值直接返回）
    const colorValue = map.getPaintProperty(layerId, paintProperty)

    if (!colorValue) {
      return null
    }

    // Mapbox 返回的颜色值通常是字符串格式，如 "rgb(255, 0, 0)" 或 "rgba(255, 0, 0, 1)"
    if (typeof colorValue === 'string') {
      return colorValue
    }

    // 如果返回的是其他类型（理论上不应该），返回 null
    return null
  } catch (error) {
    return null
  }
}

// 将 RGB 格式转换为 HEX 格式（辅助函数）
const rgbToHex = (rgb: string): string | null => {
  // 匹配 rgb(r, g, b) 或 rgba(r, g, b, a)
  const match = rgb.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/)
  if (!match) {
    return null
  }

  const r = parseInt(match[1], 10)
  const g = parseInt(match[2], 10)
  const b = parseInt(match[3], 10)

  const toHex = (n: number) => {
    const hex = n.toString(16)
    return hex.length === 1 ? '0' + hex : hex
  }

  return `#${toHex(r)}${toHex(g)}${toHex(b)}`
}

// 规范化颜色为 HEX 格式
const normalizeToHex = (color: string): string | null => {
  if (!color) return null

  // 如果已经是 hex 格式
  if (color.startsWith('#')) {
    // 验证 hex 格式（3位或6位）
    const hex = color.replace('#', '')
    if (/^[0-9A-Fa-f]{3}$/.test(hex) || /^[0-9A-Fa-f]{6}$/.test(hex)) {
      return color.toUpperCase()
    }
    return null
  }

  // 如果是 rgb 格式，转换为 hex
  if (color.startsWith('rgb')) {
    return rgbToHex(color)
  }

  // 如果没有 # 前缀，尝试添加
  if (/^[0-9A-Fa-f]{3}$/.test(color) || /^[0-9A-Fa-f]{6}$/.test(color)) {
    return '#' + color.toUpperCase()
  }

  return null
}

/** 与 Mapbox Studio 侧栏一致：展示当前 HEX（取色器 / store / 地图） */
function layerHexLine(layer: LayerConfig): string {
  const fromStore = colorSchemeStore.currentScheme.layers.find(l => l.id === layer.id)
  const raw = layerColors[layer.id] || fromStore?.color
  if (raw) {
    const h = normalizeToHex(raw)
    if (h) return h
  }
  if (originalColors[layer.id]) {
    const h = normalizeToHex(originalColors[layer.id])
    if (h) return h
  }
  const mapC = getDefaultColorFromMap(layer.id, layer.paintProperty)
  const h2 = mapC ? normalizeToHex(mapC) : null
  return h2 || '—'
}

function layerSemanticLine(layer: LayerConfig): string {
  const fromStore = colorSchemeStore.currentScheme.layers.find(l => l.id === layer.id)
  const sem = fromStore?.semantic ?? semanticForLayerId(layer.id)
  if (!sem) return ''
  const key = `mapStyle.semantics.${sem}`
  const out = t(key)
  return out === key ? sem : out
}

// 生成当前颜色方案（用于后端 / 生成方案 API）
const generateCurrentColorScheme = (): ColorScheme => {
  const allLayersConfig = getAllConfigurableLayers()
  const prevById = new Map(colorSchemeStore.currentScheme.layers.map(l => [l.id, l]))
  const allLayers: ColorSchemeItem[] = []

  allLayersConfig.forEach(layerConfig => {
    let color: string | null = null

    if (layerColors[layerConfig.id]) {
      color = layerColors[layerConfig.id]
    } else if (originalColors[layerConfig.id]) {
      color = originalColors[layerConfig.id]
    } else {
      const defaultColor = getDefaultColorFromMap(layerConfig.id, layerConfig.paintProperty)
      if (defaultColor) {
        color = defaultColor
        originalColors[layerConfig.id] = defaultColor
      } else {
        color = layerConfig.defaultColor || null
      }
    }

    let hexColor: string | null = color ? normalizeToHex(color) : null
    if (!hexColor) {
      hexColor = '#808080'
    }

    const prev = prevById.get(layerConfig.id)
    const sem = prev?.semantic ?? semanticForLayerId(layerConfig.id)
    const row: ColorSchemeItem = {
      id: layerConfig.id,
      color: hexColor,
      weight: 1,
    }
    if (sem !== undefined) {
      row.semantic = sem
    }
    allLayers.push(row)
  })

  return { layers: allLayers }
}

// 更新 Pinia store 中的颜色方案
const updateColorSchemeInStore = () => {
  const map = getMap()

  // 如果地图未加载或样式未加载，延迟更新
  if (!map || !map.isStyleLoaded()) {
    if (map) {
      map.once('load', () => {
        setTimeout(() => updateColorSchemeInStore(), 100)
      })
    }
    return
  }

  const scheme = generateCurrentColorScheme()
  colorSchemeStore.setCurrentScheme(scheme)
}

// 外部写入 currentScheme（如 pipeline 首套方案）时同步到取色器与地图
watch(
  () =>
    colorSchemeStore.currentScheme.layers.map(l => `${l.id}:${l.color}`).join('|'),
  () => {
    if (!getMap()?.isStyleLoaded()) {
      return
    }
    const configurable = new Set(getAllConfigurableLayers().map(l => l.id))
    colorSchemeStore.currentScheme.layers.forEach(l => {
      if (!configurable.has(l.id)) {
        return
      }
      const h = normalizeToHex(l.color)
      if (h) {
        layerColors[l.id] = h
      }
    })
    applyColorsToMap()
  }
)

// 组件挂载时初始化
onMounted(() => {
  // 初始化颜色方案到 Pinia store
  updateColorSchemeInStore()

  // 定期检查地图是否加载
  let checkCount = 0
  const checkMap = setInterval(() => {
    checkCount++
    const map = getMap()
    if (map) {
      if (map.isStyleLoaded()) {
        clearInterval(checkMap)
        setTimeout(() => {
          listAllLayers()
        }, 1000)
      }
    }
  }, 200) // 每200ms检查一次

  // 20秒后停止检查
  setTimeout(() => {
    clearInterval(checkMap)
    const map = getMap()
    if (map) {
      listAllLayers()
    }
  }, 20000)
})
</script>

<style scoped>
/* Mapbox Studio 侧栏风格：深色底、细分割、属性键小写标签 */
.map-style {
  --studio-bg: #2c2c2c;
  --studio-bg-elevated: #333333;
  --studio-border: rgba(255, 255, 255, 0.08);
  --studio-text: rgba(255, 255, 255, 0.92);
  --studio-text-muted: rgba(255, 255, 255, 0.45);
  --studio-accent: #4264fb;

  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--studio-bg);
  color: var(--studio-text);
}

.style-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  border-bottom: 1px solid var(--studio-border);
  background: var(--studio-bg);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.style-header h3 {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: var(--studio-text);
  text-transform: uppercase;
}

.style-content {
  flex: 1;
  overflow-y: auto;
}

.studio-collapse.category-section {
  border: none;
  --el-collapse-border-color: var(--studio-border);
}

.studio-collapse :deep(.el-collapse-item__header) {
  padding: 10px 14px;
  font-weight: 600;
  font-size: 12px;
  color: var(--studio-text);
  background: var(--studio-bg);
  border-bottom: 1px solid var(--studio-border);
}

.studio-collapse :deep(.el-collapse-item__wrap) {
  border-bottom: none;
  background: var(--studio-bg);
}

.studio-collapse :deep(.el-collapse-item__content) {
  padding: 0;
  background: var(--studio-bg);
}

.studio-collapse :deep(.el-collapse-item__arrow) {
  color: var(--studio-text-muted);
}

.layer-list {
  padding: 0;
}

.studio-layer-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--studio-border);
  background: var(--studio-bg);
}

.studio-layer-row:hover {
  background: var(--studio-bg-elevated);
}

.studio-layer-main {
  flex: 1;
  min-width: 0;
}

.studio-layer-title-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
}

.studio-layer-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--studio-text);
}

.studio-paint-key {
  font-size: 10px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  color: var(--studio-text-muted);
  text-transform: none;
  flex-shrink: 0;
}

.studio-layer-id {
  margin-top: 2px;
  font-size: 10px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  color: var(--studio-text-muted);
  word-break: break-all;
}

.studio-layer-meta {
  margin-top: 6px;
  font-size: 11px;
  color: var(--studio-text-muted);
  line-height: 1.4;
}

.studio-hex {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  color: rgba(255, 255, 255, 0.7);
}

.studio-meta-sep {
  margin: 0 4px;
  opacity: 0.5;
}

.studio-color-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  flex-shrink: 0;
}

.studio-reset-btn {
  color: var(--studio-text-muted) !important;
  padding: 2px 6px !important;
  font-size: 11px !important;
}

.studio-reset-btn:hover {
  color: var(--studio-text) !important;
}

:deep(.el-color-picker) {
  height: 28px;
}

:deep(.el-color-picker__trigger) {
  width: 28px;
  height: 28px;
  border-radius: 2px;
  border: 1px solid var(--studio-border);
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.25);
}

.generate-section {
  padding: 12px 14px;
  border-top: 1px solid var(--studio-border);
  background: #262626;
}

.generate-btn-wrap {
  display: block;
  width: 100%;
}

.generate-button {
  width: 100%;
  height: 36px;
  font-size: 12px;
  font-weight: 600;
  --el-button-bg-color: var(--studio-accent);
  --el-button-border-color: var(--studio-accent);
  --el-button-hover-bg-color: #5b7cfe;
  --el-button-hover-border-color: #5b7cfe;
}

.generate-button .el-icon {
  margin-right: 6px;
}

.generate-info {
  margin-top: 8px;
  text-align: center;
  font-size: 11px;
  color: var(--studio-text-muted);
}

.gallery-footer .gallery-hint {
  margin: 0;
  font-size: 11px;
  color: var(--studio-text-muted);
  text-align: center;
  line-height: 1.45;
}

.gallery-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.gallery-counter {
  font-size: 12px;
  font-weight: 600;
  color: var(--studio-text);
  flex-shrink: 0;
  white-space: nowrap;
}

.gallery-btn {
  flex: 1;
  min-width: 0;
}

.style-header :deep(.el-button) {
  --el-button-bg-color: transparent;
  --el-button-border-color: var(--studio-border);
  --el-button-text-color: var(--studio-text-muted);
  font-size: 11px;
}

.style-header :deep(.el-button:hover) {
  --el-button-text-color: var(--studio-text);
  --el-button-border-color: rgba(255, 255, 255, 0.2);
}
</style>
