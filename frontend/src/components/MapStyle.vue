<template>
  <div class="map-style">
    <div class="style-header">
      <h3>地图样式配置</h3>
      <div class="header-actions">
        <el-button size="small" @click="resetAllColors">重置所有</el-button>
      </div>
    </div>

    <el-scrollbar class="style-content">
      <el-collapse v-model="activeCategories" class="category-section">
        <!-- 水体类别 -->
        <el-collapse-item name="water" title="💧 水体">
          <div class="layer-list">
            <div
              v-for="layer in waterLayers"
              :key="layer.id"
              class="layer-item"
            >
              <div class="layer-info">
                <span class="layer-name">{{ layer.name }}</span>
                <span class="layer-id">{{ layer.id }}</span>
              </div>
              <div class="color-control">
                <el-color-picker
                  v-model="layerColors[layer.id]"
                  :predefine="predefineColors"
                  @change="(color) => updateLayerColor(layer.id, color, layer.paintProperty)"
                />
                <el-button
                  size="small"
                  text
                  @click="resetLayerColor(layer.id, layer.defaultColor, layer.paintProperty)"
                >
                  重置
                </el-button>
              </div>
            </div>
          </div>
        </el-collapse-item>

        <!-- 道路类别 -->
        <el-collapse-item name="roads" title="🛣️ 道路">
          <div class="layer-list">
            <div
              v-for="layer in roadLayers"
              :key="layer.id"
              class="layer-item"
            >
              <div class="layer-info">
                <span class="layer-name">{{ layer.name }}</span>
                <span class="layer-id">{{ layer.id }}</span>
              </div>
              <div class="color-control">
                <el-color-picker
                  v-model="layerColors[layer.id]"
                  :predefine="predefineColors"
                  @change="(color) => updateLayerColor(layer.id, color, layer.paintProperty)"
                />
                <el-button
                  size="small"
                  text
                  @click="resetLayerColor(layer.id, layer.defaultColor, layer.paintProperty)"
                >
                  重置
                </el-button>
              </div>
            </div>
          </div>
        </el-collapse-item>

        <!-- 建筑类别 -->
        <el-collapse-item name="buildings" title="🏢 建筑">
          <div class="layer-list">
            <div
              v-for="layer in buildingLayers"
              :key="layer.id"
              class="layer-item"
            >
              <div class="layer-info">
                <span class="layer-name">{{ layer.name }}</span>
                <span class="layer-id">{{ layer.id }}</span>
              </div>
              <div class="color-control">
                <el-color-picker
                  v-model="layerColors[layer.id]"
                  :predefine="predefineColors"
                  @change="(color) => updateLayerColor(layer.id, color, layer.paintProperty)"
                />
                <el-button
                  size="small"
                  text
                  @click="resetLayerColor(layer.id, layer.defaultColor, layer.paintProperty)"
                >
                  重置
                </el-button>
              </div>
            </div>
          </div>
        </el-collapse-item>

        <!-- 绿地/土地类别 -->
        <el-collapse-item name="green" title="🌳 绿地/土地">
          <div class="layer-list">
            <div
              v-for="layer in greenLayers"
              :key="layer.id"
              class="layer-item"
            >
              <div class="layer-info">
                <span class="layer-name">{{ layer.name }}</span>
                <span class="layer-id">{{ layer.id }}</span>
              </div>
              <div class="color-control">
                <el-color-picker
                  v-model="layerColors[layer.id]"
                  :predefine="predefineColors"
                  @change="(color) => updateLayerColor(layer.id, color, layer.paintProperty)"
                />
                <el-button
                  size="small"
                  text
                  @click="resetLayerColor(layer.id, layer.defaultColor, layer.paintProperty)"
                >
                  重置
                </el-button>
              </div>
            </div>
          </div>
        </el-collapse-item>

        <!-- 注记类别 -->
        <el-collapse-item name="labels" title="📝 注记">
          <div class="layer-list">
            <div
              v-for="layer in labelLayers"
              :key="layer.id"
              class="layer-item"
            >
              <div class="layer-info">
                <span class="layer-name">{{ layer.name }}</span>
                <span class="layer-id">{{ layer.id }}</span>
              </div>
              <div class="color-control">
                <el-color-picker
                  v-model="layerColors[layer.id]"
                  :predefine="predefineColors"
                  @change="(color) => updateLayerColor(layer.id, color, layer.paintProperty)"
                />
                <el-button
                  size="small"
                  text
                  @click="resetLayerColor(layer.id, layer.defaultColor, layer.paintProperty)"
                >
                  重置
                </el-button>
              </div>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-scrollbar>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted, inject } from 'vue'
import { ElMessage } from 'element-plus'
import type mapboxgl from 'mapbox-gl'
import { useColorSchemeStore, type ColorScheme, type ColorSchemeItem } from '@/stores'

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
  name: string
  paintProperty: 'line-color' | 'fill-color' | 'fill-outline-color' | 'text-color' | 'icon-color'
  defaultColor?: string
}

// 颜色方案类型从 store 导入

// 水体图层配置
const waterLayers: LayerConfig[] = [
  { id: 'water', name: '水体', paintProperty: 'fill-color' },
  { id: 'waterway', name: '水道', paintProperty: 'line-color' },
]

// 道路图层配置
const roadLayers: LayerConfig[] = [
  { id: 'road-pedestrian', name: '人行道', paintProperty: 'line-color' },
  { id: 'road-path', name: '小径', paintProperty: 'line-color' },
  { id: 'road-minor', name: '次要道路', paintProperty: 'line-color' },
  { id: 'road-street', name: '街道', paintProperty: 'line-color' },
  { id: 'road-secondary-tertiary', name: '二级/三级道路', paintProperty: 'line-color' },
  { id: 'road-primary', name: '主要道路', paintProperty: 'line-color' },
  { id: 'road-motorway-trunk', name: '高速公路', paintProperty: 'line-color' },
]

// 建筑图层配置
const buildingLayers: LayerConfig[] = [
  { id: 'building', name: '建筑物', paintProperty: 'fill-color' },
]

// 绿地/土地图层配置
const greenLayers: LayerConfig[] = [
  { id: 'landcover', name: '土地覆盖', paintProperty: 'fill-color' },
  { id: 'national-park', name: '国家公园', paintProperty: 'fill-color' },
  { id: 'landuse', name: '土地利用', paintProperty: 'fill-color' },
]

// 注记图层配置（使用 icon-color 而非 text-color）
const labelLayers: LayerConfig[] = [
  { id: 'waterway-label', name: '水道标签', paintProperty: 'icon-color' },
  { id: 'water-line-label', name: '水体线条标签', paintProperty: 'icon-color' },
  { id: 'water-point-label', name: '水体点标签', paintProperty: 'icon-color' },
  { id: 'road-label', name: '道路标签', paintProperty: 'icon-color' },
  { id: 'place-label', name: '地点标签', paintProperty: 'icon-color' },
  { id: 'poi-label', name: '兴趣点标签', paintProperty: 'icon-color' },
]

// 列出所有图层（用于调试）
const listAllLayers = () => {
  console.log('开始列出图层...')
  const map = getMap()
  if (!map) {
    console.log('地图未加载')
    return
  }
  
  console.log('地图已加载，检查样式状态...')
  console.log('isStyleLoaded:', map.isStyleLoaded())
  
  if (!map.isStyleLoaded()) {
    console.log('样式未加载，等待...')
    map.once('styledata', () => {
      console.log('样式数据已加载，再次尝试列出图层')
      setTimeout(() => listAllLayers(), 500)
    })
    return
  }
  
  try {
    const style = map.getStyle()
    console.log('获取样式:', style ? '成功' : '失败')
    console.log('样式类型:', typeof style)
    
    if (typeof style === 'string') {
      console.log('样式是URL字符串:', style)
      return
    }
    
    const layers = style.layers || []
    console.log('=== 所有图层列表 ===')
    console.log(`总共 ${layers.length} 个图层`)
    
    // 查找包含 water 的图层
    const waterRelated = layers.filter((l: any) => 
      l.id.toLowerCase().includes('water')
    )
    
    if (waterRelated.length > 0) {
      console.log('=== 水体相关图层（包含 water） ===')
      waterRelated.forEach((layer: any) => {
        console.log(`图层ID: "${layer.id}", 类型: ${layer.type}`)
        if (layer.paint) {
          const paintKeys = Object.keys(layer.paint)
          console.log(`  paint属性:`, paintKeys)
          if (layer.paint['fill-color']) {
            console.log(`  fill-color:`, layer.paint['fill-color'])
          }
          if (layer.paint['line-color']) {
            console.log(`  line-color:`, layer.paint['line-color'])
          }
        }
      })
      console.log('================================')
    } else {
      console.log('未找到包含 "water" 的图层')
    }
    
    // 列出所有图层ID（用于查找）
    console.log('=== 所有图层ID（前50个） ===')
    layers.slice(0, 50).forEach((layer: any, index: number) => {
      console.log(`${index + 1}. "${layer.id}" (${layer.type})`)
    })
    console.log('============================')
  } catch (e) {
    console.error('列出图层失败:', e)
  }
}

// 监听地图实例，保存 center 和 zoom
watch(
  () => mapRef?.value,
  (map) => {
    if (!map) {
      console.log('地图实例不存在')
      return
    }
    
    // 确保 map 是 Mapbox Map 实例
    if (typeof map.on !== 'function') {
      console.warn('map 不是有效的 Mapbox Map 实例:', map)
      return
    }
    
    console.log('地图实例已设置，开始初始化...')
    
    // 监听地图移动，更新保存的 center 和 zoom
    const updatePosition = () => {
      const center = map.getCenter()
      currentCenter.value = [center.lng, center.lat]
      currentZoom.value = map.getZoom()
    }
    
    map.on('moveend', updatePosition)
    map.on('zoomend', updatePosition)
    
    // 初始化时保存位置并列出图层
    const initMap = () => {
      console.log('初始化地图位置...')
      updatePosition()
      
      // 初始化颜色方案到 Pinia store
      setTimeout(() => {
        updateColorSchemeInStore()
      }, 500)
      
      // 多次尝试列出图层
      const tryListLayers = () => {
        console.log('尝试列出图层...')
        if (map.isStyleLoaded()) {
          listAllLayers()
        } else {
          console.log('样式未加载，等待 load 事件...')
          map.once('load', () => {
            console.log('load 事件触发')
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
    
    if (map.isStyleLoaded()) {
      console.log('样式已加载，立即初始化')
      initMap()
      // 保存原始颜色
      setTimeout(() => saveOriginalColors(), 500)
    } else {
      console.log('样式未加载，等待 load 事件')
      map.once('load', () => {
        console.log('load 事件触发，开始初始化')
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
        console.warn(`图层 ${layerId} 不存在于地图中，跳过保存原始颜色`)
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
            console.log(`保存图层 ${layerId} 的原始颜色: ${currentColor}`)
          }
        } else {
          console.warn(`图层 ${layerId} 的颜色值不是字符串类型:`, typeof currentColor, currentColor)
          skippedCount++
        }
      } catch (error) {
        console.warn(`获取图层 ${layerId} 的原始颜色失败:`, error)
        skippedCount++
      }
    })
    
    console.log(`保存原始颜色完成: 成功 ${savedCount} 个，跳过 ${skippedCount} 个，总计 ${allLayersConfig.length} 个可配置图层`)
  } catch (error) {
    console.warn('保存原始颜色失败:', error)
  }
}

// 应用颜色到地图（使用高性能的 setPaintProperty API）
const applyColorsToMap = () => {
  const map = getMap()
  if (!map) {
    console.warn('地图未加载')
    return
  }

  // 检查样式是否已加载
  if (!map.isStyleLoaded()) {
    console.warn('样式未加载，等待加载完成')
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
    Object.keys(layerColors).forEach((layerId) => {
      const color = layerColors[layerId]
      if (!color) return

      // 找到对应的图层配置
      const layerConfig = allLayersConfig.find(l => l.id === layerId)
      if (!layerConfig) {
        console.warn(`未找到图层配置: ${layerId}`)
        return
      }

      // 检查图层是否存在
      if (!map.getLayer(layerId)) {
        console.warn(`图层 ${layerId} 不存在于地图中`)
        return
      }

      // 转换颜色格式
      const mapboxColor = hexToRgb(color)
      
      try {
        // 使用 setPaintProperty 直接更新颜色（高性能，不会重新加载整个样式）
        map.setPaintProperty(layerId, layerConfig.paintProperty, mapboxColor)
        modifiedCount++
        console.log(`✓ 更新颜色: 图层 ${layerId} 的 ${layerConfig.paintProperty} 设置为 ${mapboxColor}`)
      } catch (error) {
        console.warn(`更新图层 ${layerId} 的颜色失败:`, error)
      }
    })

    if (modifiedCount > 0) {
      console.log(`✓ 已更新 ${modifiedCount} 个图层的颜色`)
    }
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
      console.warn(`图层 ${layerId} 不存在于地图中`)
      return
    }

    // 获取保存的原始颜色
    const originalColor = originalColors[layerId]
    if (originalColor) {
      // 恢复原始颜色
      map.setPaintProperty(layerId, paintProperty, originalColor)
      console.log(`✓ 恢复图层 ${layerId} 的原始颜色: ${originalColor}`)
    } else {
      // 如果没有保存的原始颜色，尝试从当前样式获取
      const currentColor = map.getPaintProperty(layerId, paintProperty)
      if (currentColor && typeof currentColor === 'string') {
        // 保存为原始颜色并保持当前值（可能是默认值）
        originalColors[layerId] = currentColor
      }
    }
  } catch (error) {
    console.warn(`重置图层 ${layerId} 颜色失败:`, error)
  }
}

// 更新图层颜色
const updateLayerColor = (
  layerId: string,
  color: string | null,
  paintProperty: string
) => {
  console.log('=== updateLayerColor 被调用 ===')
  console.log('图层ID:', layerId)
  console.log('颜色:', color)
  console.log('paintProperty:', paintProperty)
  
  const map = getMap()
  if (!map) {
    console.warn('地图未加载')
    return
  }
  
  // 移除调试代码以提高性能

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
  console.log('当前所有颜色设置:', { ...layerColors })
  
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
  return [
    ...waterLayers,
    ...roadLayers,
    ...buildingLayers,
    ...greenLayers,
    ...labelLayers,
  ]
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
      console.warn(`图层 ${layerId} 不存在于地图中`)
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

    // 如果返回的是其他类型（理论上不应该），尝试转换
    console.warn(`图层 ${layerId} 的 ${paintProperty} 返回了非字符串类型:`, typeof colorValue, colorValue)
    return null
  } catch (error) {
    console.warn(`获取图层 ${layerId} 的默认颜色失败:`, error)
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
      if (!hexColor) {
        console.warn(`图层 ${layerConfig.id} 的颜色格式无效，尝试其他方式: ${color}`)
      }
    }
    
    // 如果仍然无法获取颜色，使用一个默认占位颜色（确保所有图层都被包含）
    if (!hexColor) {
      // 使用灰色作为占位颜色，确保图层被包含
      hexColor = '#808080' // 灰色
      console.warn(`图层 ${layerConfig.id} 无法获取颜色值，使用占位颜色: ${hexColor}`)
    }
    
    // 确保所有图层都被添加到方案中
    allLayers.push({
      id: layerConfig.id,
      color: hexColor,
      weight: 0, // 先设为0，后面统一计算等权重
    })
    
    console.log(`图层 ${layerConfig.id}: 颜色=${hexColor}, 来源=${colorSource}`)
  })
  
  // 计算等权重
  const weight = allLayers.length > 0 ? 1 / allLayers.length : 0
  allLayers.forEach(layer => {
    layer.weight = weight
  })
  
  console.log(`生成颜色方案: 包含 ${allLayers.length} 个图层（应该包含所有 ${allLayersConfig.length} 个可配置图层）`)
  
  return {
    layers: allLayers,
  }
}

// 更新 Pinia store 中的颜色方案
const updateColorSchemeInStore = () => {
  const map = getMap()
  
  // 如果地图未加载或样式未加载，延迟更新
  if (!map || !map.isStyleLoaded()) {
    console.log('地图样式未加载，延迟更新颜色方案')
    if (map) {
      map.once('load', () => {
        setTimeout(() => updateColorSchemeInStore(), 100)
      })
    }
    return
  }
  
  const scheme = generateCurrentColorScheme()
  colorSchemeStore.setCurrentScheme(scheme)
  console.log('颜色方案已更新到 Pinia store:', scheme)
  console.log(`包含 ${scheme.layers.length} 个图层`)
}

// 组件挂载时输出调试信息
onMounted(() => {
  console.log('MapStyle 组件已挂载')
  console.log('mapRef:', mapRef)
  console.log('mapRef.value:', mapRef?.value)
  
  // 初始化颜色方案到 Pinia store
  updateColorSchemeInStore()
  
  // 定期检查地图是否加载（更频繁的检查）
  let checkCount = 0
  const checkMap = setInterval(() => {
    checkCount++
    const map = getMap()
    if (map) {
      console.log(`[${checkCount}] 地图已找到，isStyleLoaded:`, map.isStyleLoaded())
      if (map.isStyleLoaded()) {
        clearInterval(checkMap)
        console.log('样式已加载，准备列出图层')
        setTimeout(() => {
          console.log('开始列出图层...')
          listAllLayers()
        }, 1000)
      }
    } else {
      if (checkCount <= 5) {
        console.log(`[${checkCount}] 等待地图实例...`)
      }
    }
  }, 200) // 每200ms检查一次，更频繁
  
  // 20秒后停止检查
  setTimeout(() => {
    clearInterval(checkMap)
    const map = getMap()
    if (map) {
      console.log('超时检查：地图存在，强制列出图层')
      listAllLayers()
    } else {
      console.warn('超时检查：地图仍未加载')
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
  margin-bottom: 4px;
}

.layer-id {
  font-size: 11px;
  color: #909399;
  font-family: 'Courier New', monospace;
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
</style>
