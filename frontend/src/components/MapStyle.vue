<template>
  <div class="map-style">
    <div class="style-header">
      <h3>{{ t('mapStyle.title') }}</h3>
      <div class="header-actions">
        <el-button size="small" @click="resetAllColors">{{ t('mapStyle.resetAll') }}</el-button>
      </div>
    </div>

    <el-scrollbar class="style-content">
      <el-collapse v-model="activeCategories" class="category-section">
        <!-- 水体类别 -->
        <el-collapse-item name="water" :title="t('mapStyle.water')">
          <div class="layer-list">
            <div v-for="layer in waterLayers" :key="layer.id" class="layer-item">
              <div class="layer-info">
                <span class="layer-name">{{ getLayerName(layer.nameKey) }}</span>
              </div>
              <div class="color-control">
                <el-color-picker
                  v-model="layerColors[layer.id]"
                  :predefine="predefineColors"
                  @change="color => updateLayerColor(layer.id, color, layer.paintProperty)"
                />
                <el-button
                  size="small"
                  text
                  @click="resetLayerColor(layer.id, layer.defaultColor, layer.paintProperty)"
                >
                  {{ t('mapStyle.reset') }}
                </el-button>
              </div>
            </div>
          </div>
        </el-collapse-item>

        <!-- 道路类别 -->
        <el-collapse-item name="roads" :title="t('mapStyle.roads')">
          <div class="layer-list">
            <div v-for="layer in roadLayers" :key="layer.id" class="layer-item">
              <div class="layer-info">
                <span class="layer-name">{{ getLayerName(layer.nameKey) }}</span>
              </div>
              <div class="color-control">
                <el-color-picker
                  v-model="layerColors[layer.id]"
                  :predefine="predefineColors"
                  @change="color => updateLayerColor(layer.id, color, layer.paintProperty)"
                />
                <el-button
                  size="small"
                  text
                  @click="resetLayerColor(layer.id, layer.defaultColor, layer.paintProperty)"
                >
                  {{ t('mapStyle.reset') }}
                </el-button>
              </div>
            </div>
          </div>
        </el-collapse-item>

        <!-- 建筑类别 -->
        <el-collapse-item name="buildings" :title="t('mapStyle.buildings')">
          <div class="layer-list">
            <div v-for="layer in buildingLayers" :key="layer.id" class="layer-item">
              <div class="layer-info">
                <span class="layer-name">{{ getLayerName(layer.nameKey) }}</span>
              </div>
              <div class="color-control">
                <el-color-picker
                  v-model="layerColors[layer.id]"
                  :predefine="predefineColors"
                  @change="color => updateLayerColor(layer.id, color, layer.paintProperty)"
                />
                <el-button
                  size="small"
                  text
                  @click="resetLayerColor(layer.id, layer.defaultColor, layer.paintProperty)"
                >
                  {{ t('mapStyle.reset') }}
                </el-button>
              </div>
            </div>
          </div>
        </el-collapse-item>

        <!-- 绿地/土地类别 -->
        <el-collapse-item name="green" :title="t('mapStyle.green')">
          <div class="layer-list">
            <div v-for="layer in greenLayers" :key="layer.id" class="layer-item">
              <div class="layer-info">
                <span class="layer-name">{{ getLayerName(layer.nameKey) }}</span>
              </div>
              <div class="color-control">
                <el-color-picker
                  v-model="layerColors[layer.id]"
                  :predefine="predefineColors"
                  @change="color => updateLayerColor(layer.id, color, layer.paintProperty)"
                />
                <el-button
                  size="small"
                  text
                  @click="resetLayerColor(layer.id, layer.defaultColor, layer.paintProperty)"
                >
                  {{ t('mapStyle.reset') }}
                </el-button>
              </div>
            </div>
          </div>
        </el-collapse-item>

        <!-- 注记类别 -->
        <el-collapse-item name="labels" :title="t('mapStyle.labels')">
          <div class="layer-list">
            <div v-for="layer in labelLayers" :key="layer.id" class="layer-item">
              <div class="layer-info">
                <span class="layer-name">{{ getLayerName(layer.nameKey) }}</span>
              </div>
              <div class="color-control">
                <el-color-picker
                  v-model="layerColors[layer.id]"
                  :predefine="predefineColors"
                  @change="color => updateLayerColor(layer.id, color, layer.paintProperty)"
                />
                <el-button
                  size="small"
                  text
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

    <!-- 生成方案按钮区域 -->
    <div class="generate-section">
      <el-button
        type="primary"
        :loading="isGenerating"
        :disabled="!canGenerate"
        @click="handleGenerateSchemes"
        class="generate-button"
      >
        <el-icon v-if="!isGenerating"><MagicStick /></el-icon>
        {{ isGenerating ? t('mapStyle.generating') : t('mapStyle.generateSchemes') }}
      </el-button>
      <div v-if="generatedCount > 0" class="generate-info">
        {{ t('mapStyle.generatedCount', { count: generatedCount }) }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted, inject, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { MagicStick } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import type mapboxgl from 'mapbox-gl'
import { useColorSchemeStore, type ColorScheme, type ColorSchemeItem } from '@/stores'
import { schemeApi, type ColorSchemeWithId } from '@/api/scheme'

const { t } = useI18n()

type MapRef = { value: mapboxgl.Map | null }

const injected = inject<MapRef>('mapInstance', { value: null })
const mapRef = injected

// Pinia store
const colorSchemeStore = useColorSchemeStore()

// 获取地图实例
const getMap = (): mapboxgl.Map | null => {
  return mapRef?.value ?? null
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

// 图层配置接口
interface LayerConfig {
  id: string
  nameKey: string // 翻译键，而不是直接的中文名称
  paintProperty: 'line-color' | 'fill-color' | 'fill-outline-color' | 'text-color' | 'icon-color'
  defaultColor?: string
}

// 获取图层显示名称（国际化）
const getLayerName = (nameKey: string): string => {
  return t(`mapStyle.layers.${nameKey}`)
}

// 颜色方案类型从 store 导入

// 水体图层配置
const waterLayers: LayerConfig[] = [
  { id: 'water', nameKey: 'water', paintProperty: 'fill-color' },
  { id: 'waterway', nameKey: 'waterway', paintProperty: 'line-color' },
]

// 道路图层配置
const roadLayers: LayerConfig[] = [
  { id: 'road-pedestrian', nameKey: 'roadPedestrian', paintProperty: 'line-color' },
  { id: 'road-path', nameKey: 'roadPath', paintProperty: 'line-color' },
  { id: 'road-minor', nameKey: 'roadMinor', paintProperty: 'line-color' },
  { id: 'road-street', nameKey: 'roadStreet', paintProperty: 'line-color' },
  { id: 'road-secondary-tertiary', nameKey: 'roadSecondaryTertiary', paintProperty: 'line-color' },
  { id: 'road-primary', nameKey: 'roadPrimary', paintProperty: 'line-color' },
  { id: 'road-motorway-trunk', nameKey: 'roadMotorwayTrunk', paintProperty: 'line-color' },
]

// 建筑图层配置
const buildingLayers: LayerConfig[] = [
  { id: 'building', nameKey: 'building', paintProperty: 'fill-color' },
]

// 绿地/土地图层配置
const greenLayers: LayerConfig[] = [
  { id: 'landcover', nameKey: 'landcover', paintProperty: 'fill-color' },
  { id: 'national-park', nameKey: 'nationalPark', paintProperty: 'fill-color' },
  { id: 'landuse', nameKey: 'landuse', paintProperty: 'fill-color' },
]

// 注记图层配置（使用 icon-color 而非 text-color）
const labelLayers: LayerConfig[] = [
  { id: 'waterway-label', nameKey: 'waterwayLabel', paintProperty: 'icon-color' },
  { id: 'water-line-label', nameKey: 'waterLineLabel', paintProperty: 'icon-color' },
  { id: 'water-point-label', nameKey: 'waterPointLabel', paintProperty: 'icon-color' },
  { id: 'road-label', nameKey: 'roadLabel', paintProperty: 'icon-color' },
  { id: 'place-label', nameKey: 'placeLabel', paintProperty: 'icon-color' },
  { id: 'poi-label', nameKey: 'poiLabel', paintProperty: 'icon-color' },
]

// 列出所有图层（用于调试）
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
  () => mapRef?.value,
  map => {
    if (!map) {
      return
    }

    // 确保 map 是 Mapbox Map 实例
    // 检查 map 对象是否有 Mapbox Map 的关键方法
    // 处理 Proxy 对象的情况
    const actualMap = map?.value || map
    if (!actualMap || typeof actualMap.on !== 'function' || typeof actualMap.getCenter !== 'function' || typeof actualMap.getZoom !== 'function') {
      return
    }
    
    // 使用实际的地图实例
    const mapInstance = actualMap

    // 监听地图移动，更新保存的 center 和 zoom
    const updatePosition = () => {
      const center = mapInstance.getCenter()
      currentCenter.value = [center.lng, center.lat]
      currentZoom.value = mapInstance.getZoom()
    }

    mapInstance.on('moveend', updatePosition)
    mapInstance.on('zoomend', updatePosition)

    // 初始化时保存位置并列出图层
    const initMap = () => {
      updatePosition()

      // 初始化颜色方案到 Pinia store
      setTimeout(() => {
        updateColorSchemeInStore()
      }, 500)

      // 多次尝试列出图层
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

      // 立即尝试
      tryListLayers()

      // 延迟尝试（防止事件已触发）
      setTimeout(() => {
        tryListLayers()
      }, 2000)

      setTimeout(() => {
        tryListLayers()
      }, 5000)
    }

    // 初始化地图
    if (mapInstance.isStyleLoaded && mapInstance.isStyleLoaded()) {
      initMap()
      // 保存原始颜色
      setTimeout(() => saveOriginalColors(), 500)
    } else if (mapInstance.once) {
      mapInstance.once('load', () => {
        initMap()
        // 保存原始颜色
        setTimeout(() => saveOriginalColors(), 500)
      })
    }
  },
  { immediate: true }
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

// 获取所有可配置的图层配置列表
const getAllConfigurableLayers = (): LayerConfig[] => {
  return [...waterLayers, ...roadLayers, ...buildingLayers, ...greenLayers, ...labelLayers]
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

// 生成当前颜色方案（用于遗传算法）
// 包含所有可配置的图层，未修改的使用 Mapbox 默认颜色，占比默认等权重
const generateCurrentColorScheme = (): ColorScheme => {
  const allLayersConfig = getAllConfigurableLayers()

  // 包含所有图层的颜色配置（必须包含所有可配置的图层）
  const allLayers: ColorSchemeItem[] = []

  allLayersConfig.forEach(layerConfig => {
    let color: string | null = null
    let colorSource = 'unknown'

    // 优先使用用户设置的颜色
    if (layerColors[layerConfig.id]) {
      color = layerColors[layerConfig.id]
      colorSource = 'user'
    } else {
      // 如果没有用户设置，优先使用保存的原始颜色
      if (originalColors[layerConfig.id]) {
        color = originalColors[layerConfig.id]
        colorSource = 'original'
      } else {
        // 如果原始颜色未保存，从地图中获取默认颜色
        const defaultColor = getDefaultColorFromMap(layerConfig.id, layerConfig.paintProperty)
        if (defaultColor) {
          color = defaultColor
          colorSource = 'mapbox'
          // 同时保存为原始颜色，以便下次使用
          originalColors[layerConfig.id] = defaultColor
        } else {
          // 如果都无法获取，使用配置中的默认颜色（如果有）
          color = layerConfig.defaultColor || null
          colorSource = 'config'
        }
      }
    }

    // 规范化颜色为 HEX 格式
    let hexColor: string | null = null
    if (color) {
      hexColor = normalizeToHex(color)
    }

    // 如果仍然无法获取颜色，使用一个默认占位颜色（确保所有图层都被包含）
    if (!hexColor) {
      // 使用灰色作为占位颜色，确保图层被包含
      hexColor = '#808080' // 灰色
    }

    // 确保所有图层都被添加到方案中
    allLayers.push({
      id: layerConfig.id,
      color: hexColor,
      weight: 0, // 先设为0，后面统一计算等权重
    })
  })

  // 计算等权重
  const weight = allLayers.length > 0 ? 1 / allLayers.length : 0
  allLayers.forEach(layer => {
    layer.weight = weight
  })

  return {
    layers: allLayers,
  }
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

// 生成方案相关状态
const isGenerating = ref(false)
const generatedCount = ref(0)

// 是否可以生成方案（当前方案不为空）
const canGenerate = computed(() => {
  const scheme = colorSchemeStore.currentScheme
  return scheme.layers.length > 0
})

// 生成方案处理函数
const handleGenerateSchemes = async () => {
  const currentScheme = colorSchemeStore.currentScheme
  
  if (!currentScheme || currentScheme.layers.length === 0) {
    ElMessage.warning(t('mapStyle.noCurrentScheme'))
    return
  }

  isGenerating.value = true
  generatedCount.value = 0

  try {
    const response = await schemeApi.generateSchemes({
      currentScheme,
      count: 5, // 生成 5 个方案
    })

    // 将生成的方案（包含 id）保存到 store
    colorSchemeStore.setColorSchemes(response.schemes)
    generatedCount.value = response.schemes.length

    ElMessage.success(
      t('mapStyle.generateSuccess', { count: response.schemes.length })
    )
  } catch (error) {
    console.error('生成方案失败:', error)
    ElMessage.error(
      error instanceof Error
        ? error.message
        : t('mapStyle.generateError')
    )
  } finally {
    isGenerating.value = false
  }
}

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
.map-style {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.style-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.style-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.style-content {
  flex: 1;
  overflow-y: auto;
}

.category-section {
  border: none;
}

.category-section :deep(.el-collapse-item__header) {
  padding: 12px 16px;
  font-weight: 600;
  font-size: 14px;
  color: #303133;
  border-bottom: 1px solid #f0f0f0;
}

.category-section :deep(.el-collapse-item__content) {
  padding: 0;
}

.layer-list {
  padding: 8px;
}

.layer-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  margin-bottom: 8px;
  background: #f5f7fa;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.layer-item:hover {
  background: #ebedf0;
}

.layer-info {
  display: flex;
  flex-direction: column;
  flex: 1;
  margin-right: 12px;
}

.layer-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.color-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

:deep(.el-color-picker) {
  height: 32px;
}

:deep(.el-color-picker__trigger) {
  width: 40px;
  height: 32px;
  border-radius: 4px;
}

.generate-section {
  padding: 16px;
  border-top: 1px solid #e4e7ed;
  background: #fafafa;
}

.generate-button {
  width: 100%;
  height: 40px;
  font-size: 14px;
  font-weight: 500;
}

.generate-button .el-icon {
  margin-right: 6px;
}

.generate-info {
  margin-top: 8px;
  text-align: center;
  font-size: 12px;
  color: #909399;
}
</style>
