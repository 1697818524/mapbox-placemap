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
      </el-collapse>
    </el-scrollbar>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted, inject } from 'vue'
import { ElMessage } from 'element-plus'
import type mapboxgl from 'mapbox-gl'

type MapRef = { value: mapboxgl.Map | null }

const injected = inject<MapRef>('mapInstance', { value: null })
const mapRef = injected

// 获取地图实例
const getMap = (): mapboxgl.Map | null => {
  return mapRef?.value ?? null
}

// 展开的类别
const activeCategories = ref<string[]>(['water'])

// 图层颜色状态（保存用户设置的颜色）
const layerColors = reactive<Record<string, string>>({})

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
  paintProperty: 'line-color' | 'fill-color' | 'fill-outline-color' | 'text-color'
  defaultColor?: string
}

// 水体图层配置
// 注意：Mapbox Streets v12 中水体图层可能是 'waterway' 或其他名称
// 如果 'water' 不工作，请查看控制台输出的可用图层列表
const waterLayers: LayerConfig[] = [
  { id: 'water', name: '水体', paintProperty: 'fill-color' },
  { id: 'waterway', name: '水道', paintProperty: 'line-color' },
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
    } else {
      console.log('样式未加载，等待 load 事件')
      map.once('load', () => {
        console.log('load 事件触发，开始初始化')
        initMap()
      })
    }
  },
  { immediate: true }
)

// 重新加载地图并应用颜色
const reloadMapWithColors = () => {
  const map = getMap()
  if (!map) {
    console.warn('地图未加载')
    return
  }

  try {
    // 保存当前的 center 和 zoom
    const center = map.getCenter()
    currentCenter.value = [center.lng, center.lat]
    currentZoom.value = map.getZoom()
    
    console.log('保存当前位置:', currentCenter.value, '缩放:', currentZoom.value)

    // 检查样式是否已加载
    if (!map.isStyleLoaded()) {
      console.warn('样式未加载，等待加载完成')
      map.once('load', () => {
        setTimeout(() => reloadMapWithColors(), 100)
      })
      return
    }

    // 获取当前样式
    const style = map.getStyle()
    console.log('获取样式:', style ? '成功' : '失败')
    console.log('样式类型:', typeof style)
    
    // 如果样式是字符串（URL），需要先加载
    if (typeof style === 'string') {
      console.warn('样式是URL字符串，无法直接修改')
      return
    }
    
    // 创建样式副本并修改颜色
    const modifiedStyle = JSON.parse(JSON.stringify(style))
    console.log('样式副本创建成功，图层数量:', modifiedStyle.layers?.length)
    
    let modifiedCount = 0
    
    // 应用所有已设置的颜色
    Object.keys(layerColors).forEach((layerId) => {
      const color = layerColors[layerId]
      if (!color) return

      // 找到对应的图层配置
      const layerConfig = waterLayers.find(l => l.id === layerId)
      if (!layerConfig) {
        console.warn(`未找到图层配置: ${layerId}`)
        return
      }

      // 找到样式中的图层
      const styleLayer = modifiedStyle.layers?.find((l: any) => l.id === layerId)
      if (!styleLayer) {
        console.warn(`样式中未找到图层: ${layerId}`)
        // 列出所有图层ID（前10个）
        const allLayerIds = modifiedStyle.layers?.slice(0, 10).map((l: any) => l.id) || []
        console.log('前10个图层ID:', allLayerIds)
        return
      }
      
      if (!styleLayer.paint) {
        console.warn(`图层 ${layerId} 没有 paint 属性`)
        return
      }

      // 转换颜色格式
      const mapboxColor = hexToRgb(color)
      
      // 更新样式中的颜色
      styleLayer.paint[layerConfig.paintProperty] = mapboxColor
      modifiedCount++
      
      console.log(`✓ 修改样式: 图层 ${layerId} 的 ${layerConfig.paintProperty} 设置为 ${mapboxColor}`)
    })

    if (modifiedCount === 0) {
      console.warn('没有找到任何图层进行修改')
      return
    }

    console.log(`准备重新加载地图，修改了 ${modifiedCount} 个图层`)

    // 重新加载地图样式
    map.setStyle(modifiedStyle)

    // 等待样式加载完成后恢复 center 和 zoom
    const onLoad = () => {
      if (currentCenter.value && currentZoom.value !== null) {
        map.jumpTo({
          center: currentCenter.value,
          zoom: currentZoom.value,
        })
        console.log('✓ 地图重新加载完成，已恢复位置和缩放')
        map.off('load', onLoad)
      }
    }
    
    map.on('load', onLoad)
  } catch (error) {
    console.error('重新加载地图失败:', error)
    console.error('错误详情:', error)
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
  
  console.log('地图已获取，isStyleLoaded:', map.isStyleLoaded())
  
  // 先列出图层（用于调试）
  if (map.isStyleLoaded()) {
    listAllLayers()
  }

  if (!color) {
    // 如果颜色为空，删除该图层的颜色设置
    delete layerColors[layerId]
    // 重新加载地图（使用默认颜色）
    reloadMapWithColors()
    return
  }

  // 保存颜色状态
  layerColors[layerId] = color
  console.log('当前所有颜色设置:', { ...layerColors })
  
  // 重新加载地图并应用颜色
  reloadMapWithColors()
}

// 重置单个图层颜色
const resetLayerColor = (
  layerId: string,
  defaultColor: string | undefined,
  paintProperty: string
) => {
  // 删除该图层的颜色设置
  delete layerColors[layerId]
  
  // 重新加载地图（使用默认颜色）
  reloadMapWithColors()
}

// 重置所有颜色
const resetAllColors = () => {
  // 清空所有颜色设置
  Object.keys(layerColors).forEach(key => {
    delete layerColors[key]
  })
  
  // 重新加载地图（使用默认颜色）
  reloadMapWithColors()
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

// 组件挂载时输出调试信息
onMounted(() => {
  console.log('MapStyle 组件已挂载')
  console.log('mapRef:', mapRef)
  console.log('mapRef.value:', mapRef?.value)
  
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
