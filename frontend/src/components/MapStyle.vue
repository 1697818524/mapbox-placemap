<template>
  <div class="map-style">
    <div class="style-header">
      <h3>{{ t('mapStyle.title') }}</h3>
      <div class="header-actions">
        <el-checkbox v-model="showLabelLayers" size="small">显示标签</el-checkbox>
        <el-button size="small" @click="resetAllColors">{{ t('mapStyle.resetAll') }}</el-button>
      </div>
    </div>

    <el-scrollbar class="style-content">
      <el-collapse v-model="activeCategories" class="category-section studio-collapse">
        <el-collapse-item
          v-for="category in styleCategories"
          :key="category.name"
          :name="category.name"
          :title="category.title"
        >
          <div class="layer-list">
            <div v-for="layer in category.layers" :key="layer.id" class="studio-layer-row">
              <div class="studio-layer-main">
                <span class="studio-color-chip" :style="{ backgroundColor: displayColor(layer) }"></span>
                <span class="studio-layer-name">{{ getLayerName(layer.nameKey) }}</span>
                <span class="studio-hex">{{ layerHexLine(layer) }}</span>
              </div>
              <div class="studio-color-actions">
                <el-color-picker
                  v-model="layerColors[layer.id]"
                  :predefine="predefineColors"
                  size="small"
                  @change="(color: string | null) => updateLayerColor(layer, color)"
                />
                <el-button size="small" text class="studio-reset-btn" @click="resetLayerColor(layer)">
                  ↺
                </el-button>
              </div>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-scrollbar>

    <el-dialog v-model="schemeDialogVisible" width="560px" class="scheme-dialog" :show-close="!isGenerating">
      <template #header>
        <div class="scheme-dialog-head">
          <h3>生成方案参数</h3>
          <p>选择候选色使用方式，并设置遗传搜索参数。</p>
        </div>
      </template>

      <div class="scheme-form">
        <div class="mode-row">
          <button
            type="button"
            class="mode-card"
            :class="{ active: schemeMode === 'local' }"
            @click="schemeMode = 'local'"
          >
            <strong>局部候选</strong>
            <span>样式优先使用对应语义的候选色；缺少语义时可在下方改派。</span>
          </button>
          <button
            type="button"
            class="mode-card"
            :class="{ active: schemeMode === 'global' }"
            @click="schemeMode = 'global'"
          >
            <strong>全局候选</strong>
            <span>每个样式都可以从所有语义候选色中取色。</span>
          </button>
        </div>

        <div class="number-grid">
          <label>
            <span>种群数</span>
            <el-input-number v-model="schemePopulation" :min="8" :max="200" :step="4" size="small" />
          </label>
          <label>
            <span>迭代次数</span>
            <el-input-number v-model="schemeGenerations" :min="1" :max="200" :step="5" size="small" />
          </label>
        </div>

        <div v-if="schemeMode === 'local'" class="semantic-editor">
          <div class="semantic-editor-head">
            <strong>局部语义映射</strong>
            <span>如果某个样式没有对应候选色，可以临时赋予其他语义。</span>
          </div>
          <div v-for="layer in modelLayers" :key="layer.id" class="semantic-row">
            <span>{{ getLayerName(layer.nameKey) }}</span>
            <el-select v-model="layerSemanticDraft[layer.id]" size="small">
              <el-option
                v-for="option in semanticOptionsWithState"
                :key="option.value"
                :label="option.label"
                :value="option.value"
                :disabled="option.disabled"
              />
            </el-select>
          </div>
          <p v-if="availableSemantics.length" class="semantic-hint">
            灰色语义表示当前样本集没有候选色。可用候选：{{ availableSemantics.join('、') }}
          </p>
        </div>
      </div>

      <template #footer>
        <el-button :disabled="isGenerating" @click="schemeDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="isGenerating" @click="confirmGenerateSchemes">
          {{ isGenerating ? t('mapStyle.generating') : '开始生成' }}
        </el-button>
      </template>
    </el-dialog>

    <div v-if="footerMode === 'generate'" class="generate-section">
      <el-tooltip :content="generateBlockedReason" placement="top" :disabled="canGenerate">
        <span class="generate-btn-wrap">
          <el-button
            type="primary"
            :loading="isGenerating"
            :disabled="!canGenerate"
            class="generate-button"
            @click="openSchemeDialog"
          >
            <el-icon v-if="!isGenerating"><MagicStick /></el-icon>
            {{ isGenerating ? t('mapStyle.generating') : t('mapStyle.generateSchemes') }}
          </el-button>
        </span>
      </el-tooltip>
    </div>

    <div v-else class="generate-section gallery-footer">
      <p v-if="colorSchemes.length === 0" class="gallery-hint">{{ t('mapStyle.galleryEmpty') }}</p>
      <div v-else class="gallery-row">
        <el-button size="small" class="gallery-btn" :disabled="!canGalleryPrev" @click="galleryPrev">
          {{ t('generatePage.prevScheme') }}
        </el-button>
        <span class="gallery-counter">{{ galleryCounter }}</span>
        <el-button size="small" class="gallery-btn" :disabled="!canGalleryNext" @click="galleryNext">
          {{ t('generatePage.nextScheme') }}
        </el-button>
      </div>
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
import { semanticForLayerId } from '@/config/placemapSemantics'
import {
  baseLayers,
  waterLayers,
  waterLabelLayers,
  roadLevel1Layers,
  roadLevel2Layers,
  roadLevel3Layers,
  roadLabelLayers,
  buildingLayers,
  greenLayers,
  landmarkLabelLayers,
  getAllConfigurableLayers,
  getLayerTargets,
  type LayerConfig,
  type LayerTarget,
} from '@/config/mapStyleLayers'
import { useColorSchemeStore, type ColorScheme, type ColorSchemeItem } from '@/stores'
import { schemeApi } from '@/api/scheme'
import { pipelineApi } from '@/api/pipeline'
import type { MapboxMapInstance } from '@/composables'

const props = withDefaults(
  defineProps<{
    footerMode?: 'generate' | 'gallery'
  }>(),
  { footerMode: 'generate' },
)

const { t } = useI18n()
const router = useRouter()
const mapInstanceRef = inject<Ref<MapboxMapInstance | null>>('mapInstance')
if (!mapInstanceRef) {
  throw new Error('mapInstance not provided')
}

const colorSchemeStore = useColorSchemeStore()
const { colorSchemes, selectedSchemeIndex, schemeGenerationReady } = storeToRefs(colorSchemeStore)
const getMap = (): MapboxMapInstance | null => mapInstanceRef.value

const showLabelLayers = ref(false)
const activeCategories = ref<string[]>(['base', 'water', 'roadLevel1', 'roadLevel2', 'roadLevel3', 'buildings', 'green'])
const layerColors = reactive<Record<string, string>>({})
const originalColors = reactive<Record<string, string>>({})

const styleCategories = computed(() => {
  const categories: Array<{ name: string; title: string; layers: LayerConfig[] }> = [
    { name: 'base', title: '背景', layers: baseLayers },
    {
      name: 'water',
      title: '水体',
      layers: showLabelLayers.value ? [...waterLayers, ...waterLabelLayers] : waterLayers,
    },
    { name: 'roadLevel1', title: '一级道路', layers: roadLevel1Layers },
    {
      name: 'roadLevel2',
      title: '二级道路',
      layers: showLabelLayers.value ? [...roadLevel2Layers, ...roadLabelLayers] : roadLevel2Layers,
    },
    { name: 'roadLevel3', title: '三级道路', layers: roadLevel3Layers },
    { name: 'buildings', title: t('mapStyle.buildings'), layers: buildingLayers },
    { name: 'green', title: t('mapStyle.green'), layers: greenLayers },
  ]

  if (showLabelLayers.value) {
    categories.push({ name: 'landmarkLabels', title: '地名 / 兴趣点', layers: landmarkLabelLayers })
  }

  return categories
})

const modelLayers = computed(() => getAllConfigurableLayers({ includeLabels: false }))
const allKnownLayers = computed(() => getAllConfigurableLayers({ includeLabels: true }))

const predefineColors = [
  '#F3EFEC',
  '#8ECAD6',
  '#7D8286',
  '#F7D96C',
  '#24DD91',
  '#D4CBBE',
  '#EF6F6C',
  '#6D8EEB',
  '#A98DF4',
  '#FFFFFF',
  '#2F3640',
  '#808080',
]

const canGalleryPrev = computed(() => colorSchemes.value.length > 0 && selectedSchemeIndex.value > 0)
const canGalleryNext = computed(() => colorSchemes.value.length > 0 && selectedSchemeIndex.value < colorSchemes.value.length - 1)
const galleryCounter = computed(() => {
  const n = colorSchemes.value.length
  if (!n) return ''
  return t('generatePage.schemeCounter', {
    current: selectedSchemeIndex.value + 1,
    total: n,
  })
})

const isGenerating = ref(false)
const schemeDialogVisible = ref(false)
const schemeMode = ref<'local' | 'global'>('local')
const schemePopulation = ref(40)
const schemeGenerations = ref(25)
const availableSemantics = ref<string[]>([])
const layerSemanticDraft = reactive<Record<string, string>>({})
const semanticOptions = [
  { label: '底色', value: 'base' },
  { label: '水体', value: 'water' },
  { label: '路网', value: 'roadnet' },
  { label: '建筑', value: 'architecture' },
  { label: '绿地/土地', value: 'green' },
  { label: '地标', value: 'landmark' },
]
const semanticOptionsWithState = computed(() => {
  const available = new Set(availableSemantics.value)
  return semanticOptions.map(option => ({
    ...option,
    disabled: available.size > 0 && !available.has(option.value),
  }))
})
const canGenerate = computed(() => props.footerMode === 'generate' && colorSchemeStore.currentScheme.layers.length > 0)
const generateBlockedReason = computed(() => {
  if (props.footerMode !== 'generate') return ''
  if (colorSchemeStore.currentScheme.layers.length === 0) return t('mapStyle.noCurrentScheme')
  return ''
})

function galleryPrev() {
  colorSchemeStore.setSelectedSchemeIndex(selectedSchemeIndex.value - 1)
}

function galleryNext() {
  colorSchemeStore.setSelectedSchemeIndex(selectedSchemeIndex.value + 1)
}

function requestPipelineBuild(): Promise<boolean> {
  return new Promise((resolve, reject) => {
    window.dispatchEvent(new CustomEvent('placemap:build-samples', { detail: { resolve, reject } }))
  })
}

function syncSemanticDraft() {
  modelLayers.value.forEach(layer => {
    layerSemanticDraft[layer.id] = layerSemanticDraft[layer.id] || semanticForLayerId(layer.id) || 'green'
  })
}

async function loadAvailableSemantics() {
  const jobId = colorSchemeStore.lastPipelineJobId
  if (!jobId) {
    availableSemantics.value = []
    return
  }
  try {
    const response = await pipelineApi.getJobPaletteSemantics(jobId)
    availableSemantics.value = response.semantics
  } catch (error) {
    console.warn('Failed to load palette semantics:', error)
    availableSemantics.value = []
  }
}

async function openSchemeDialog() {
  const currentScheme = colorSchemeStore.currentScheme
  if (!currentScheme.layers.length) {
    ElMessage.warning(t('mapStyle.noCurrentScheme'))
    return
  }
  syncSemanticDraft()
  await loadAvailableSemantics()
  schemeDialogVisible.value = true
}

async function confirmGenerateSchemes() {
  const currentScheme: ColorScheme = {
    layers: colorSchemeStore.currentScheme.layers.map(layer => ({
      ...layer,
      semantic:
        schemeMode.value === 'local'
          ? layerSemanticDraft[layer.id] || layer.semantic
          : layer.semantic,
    })),
  }
  if (!currentScheme.layers.length) {
    ElMessage.warning(t('mapStyle.noCurrentScheme'))
    return
  }
  isGenerating.value = true
  try {
    if (!schemeGenerationReady.value) {
      const ready = await requestPipelineBuild()
      if (!ready) return
    }

    const response = await schemeApi.generateSchemes({
      currentScheme,
      count: 5,
      jobId: colorSchemeStore.lastPipelineJobId || undefined,
      population: schemePopulation.value,
      generations: schemeGenerations.value,
      semanticMode: schemeMode.value,
      layerSemantics: schemeMode.value === 'local' ? { ...layerSemanticDraft } : {},
    })
    colorSchemeStore.setColorSchemes(response.schemes)
    ElMessage.success(t('mapStyle.generateSuccess', { count: response.schemes.length }))
    schemeDialogVisible.value = false
    await router.push('/generate')
  } catch (error) {
    console.error('生成方案失败:', error)
    ElMessage.error(error instanceof Error ? error.message : t('mapStyle.generateError'))
  } finally {
    isGenerating.value = false
  }
}

const getLayerName = (nameKey: string): string => {
  const key = `mapStyle.layers.${nameKey}`
  const label = t(key)
  return label === key ? nameKey : label
}

const targetKey = (target: LayerTarget): string => `${target.id}:${target.paintProperty}`

const uniqueTargets = (targets: LayerTarget[]): LayerTarget[] => {
  const seen = new Set<string>()
  return targets.filter(target => {
    const key = targetKey(target)
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

const mapStyleLayers = (): Array<{ id: string; type?: string }> => {
  const map = getMap()
  if (!map || !map.isStyleLoaded()) return []

  try {
    const style = map.getStyle()
    if (!style || typeof style === 'string') return []
    return (style.layers || []) as Array<{ id: string; type?: string }>
  } catch (error) {
    void error
    return []
  }
}

const resolveLayerTargets = (layer: LayerConfig): LayerTarget[] => {
  const explicit = getLayerTargets(layer)
  const dynamic: LayerTarget[] = []

  mapStyleLayers().forEach(styleLayer => {
    const id = styleLayer.id
    const lower = id.toLowerCase()
    const type = styleLayer.type
    const isLabel = lower.includes('label') || lower.includes('symbol')
    const isRoadLine = lower.includes('road') && type === 'line' && !isLabel

    if (layer.id === 'background') {
      if (id === 'background') dynamic.push({ id, paintProperty: 'background-color' })
      if (id === 'land' && type === 'fill') dynamic.push({ id, paintProperty: 'fill-color' })
      return
    }

    if (layer.id === 'water') {
      if (lower.includes('water') && !isLabel) {
        if (type === 'fill') dynamic.push({ id, paintProperty: 'fill-color' })
        if (type === 'line') dynamic.push({ id, paintProperty: 'line-color' })
      }
      return
    }

    if (layer.id === 'road-level-1' && isRoadLine) {
      if (lower.includes('motorway') || lower.includes('trunk') || lower.includes('primary')) {
        dynamic.push({ id, paintProperty: 'line-color' })
      }
      return
    }

    if (layer.id === 'road-level-2' && isRoadLine) {
      if (lower.includes('secondary') || lower.includes('tertiary') || lower.includes('street')) {
        dynamic.push({ id, paintProperty: 'line-color' })
      }
      return
    }

    if (layer.id === 'road-level-3' && isRoadLine) {
      if (
        lower.includes('minor') ||
        lower.includes('path') ||
        lower.includes('pedestrian') ||
        lower.includes('service') ||
        lower.includes('step')
      ) {
        dynamic.push({ id, paintProperty: 'line-color' })
      }
      return
    }

    if (layer.id === 'building' && lower.includes('building')) {
      if (type === 'fill') dynamic.push({ id, paintProperty: 'fill-color' })
      if (type === 'fill-extrusion') dynamic.push({ id, paintProperty: 'fill-extrusion-color' })
    }
  })

  return uniqueTargets([...explicit, ...dynamic])
}

const getDefaultColorFromMap = (target: LayerTarget): string | null => {
  const map = getMap()
  if (!map || !map.isStyleLoaded() || !map.getLayer(target.id)) return null

  try {
    const colorValue = map.getPaintProperty(target.id, target.paintProperty as any)
    return typeof colorValue === 'string' ? colorValue : null
  } catch (error) {
    void error
    return null
  }
}

const saveOriginalColors = () => {
  const map = getMap()
  if (!map || !map.isStyleLoaded()) return

  allKnownLayers.value.forEach(layer => {
    resolveLayerTargets(layer).forEach(target => {
      const key = targetKey(target)
      if (originalColors[key]) return
      const color = getDefaultColorFromMap(target)
      if (color) originalColors[key] = color
    })
  })
}

const setTargetColor = (target: LayerTarget, color: string) => {
  const map = getMap()
  if (!map || !map.isStyleLoaded() || !map.getLayer(target.id)) return

  try {
    map.setPaintProperty(target.id, target.paintProperty as any, hexToRgb(color))
  } catch (error) {
    void error
  }
}

const applyColorsToMap = () => {
  const map = getMap()
  if (!map) return

  if (!map.isStyleLoaded()) {
    map.once('load', () => {
      setTimeout(() => applyColorsToMap(), 100)
    })
    return
  }

  const layerById = new Map(modelLayers.value.map(layer => [layer.id, layer]))
  Object.entries(layerColors).forEach(([layerId, color]) => {
    const layer = layerById.get(layerId)
    if (!layer || !color) return
    resolveLayerTargets(layer).forEach(target => setTargetColor(target, color))
  })
}

const resetTargetColorToDefault = (target: LayerTarget) => {
  const map = getMap()
  if (!map || !map.isStyleLoaded() || !map.getLayer(target.id)) return

  try {
    const originalColor = originalColors[targetKey(target)]
    if (originalColor) {
      map.setPaintProperty(target.id, target.paintProperty as any, originalColor)
    }
  } catch (error) {
    void error
  }
}

const updateLayerColor = (layer: LayerConfig, color: string | null) => {
  if (!color) {
    delete layerColors[layer.id]
    resolveLayerTargets(layer).forEach(resetTargetColorToDefault)
  } else {
    layerColors[layer.id] = color
    resolveLayerTargets(layer).forEach(target => setTargetColor(target, color))
  }
  updateColorSchemeInStore()
}

const resetLayerColor = (layer: LayerConfig) => {
  delete layerColors[layer.id]
  resolveLayerTargets(layer).forEach(resetTargetColorToDefault)
  updateColorSchemeInStore()
}

const resetAllColors = () => {
  modelLayers.value.forEach(layer => {
    delete layerColors[layer.id]
    resolveLayerTargets(layer).forEach(resetTargetColorToDefault)
  })
  updateColorSchemeInStore()
}

const hexToRgb = (hex: string): string => {
  if (hex.startsWith('rgba') || hex.startsWith('rgb')) return hex
  const cleanHex = hex.replace('#', '')
  const r = parseInt(cleanHex.substring(0, 2), 16)
  const g = parseInt(cleanHex.substring(2, 4), 16)
  const b = parseInt(cleanHex.substring(4, 6), 16)
  return `rgb(${r}, ${g}, ${b})`
}

const rgbToHex = (rgb: string): string | null => {
  const match = rgb.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/)
  if (!match) return null
  const r = parseInt(match[1]!, 10)
  const g = parseInt(match[2]!, 10)
  const b = parseInt(match[3]!, 10)
  const toHex = (n: number) => n.toString(16).padStart(2, '0')
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`.toUpperCase()
}

const normalizeToHex = (color: string): string | null => {
  if (!color) return null
  if (color.startsWith('#')) {
    const hex = color.replace('#', '')
    return /^[0-9A-Fa-f]{3}$/.test(hex) || /^[0-9A-Fa-f]{6}$/.test(hex)
      ? color.toUpperCase()
      : null
  }
  if (color.startsWith('rgb')) return rgbToHex(color)
  if (/^[0-9A-Fa-f]{3}$/.test(color) || /^[0-9A-Fa-f]{6}$/.test(color)) {
    return `#${color.toUpperCase()}`
  }
  return null
}

function layerHexLine(layer: LayerConfig): string {
  const fromStore = colorSchemeStore.currentScheme.layers.find(l => l.id === layer.id)
  const raw = layerColors[layer.id] || fromStore?.color
  if (raw) {
    const h = normalizeToHex(raw)
    if (h) return h
  }

  for (const target of resolveLayerTargets(layer)) {
    const original = originalColors[targetKey(target)]
    if (original) {
      const h = normalizeToHex(original)
      if (h) return h
    }
    const mapColor = getDefaultColorFromMap(target)
    const h = mapColor ? normalizeToHex(mapColor) : null
    if (h) return h
  }

  return layer.defaultColor || '-'
}

function displayColor(layer: LayerConfig): string {
  const h = layerHexLine(layer)
  return h.startsWith('#') ? h : '#d8dee8'
}

const generateCurrentColorScheme = (): ColorScheme => {
  const prevById = new Map(colorSchemeStore.currentScheme.layers.map(l => [l.id, l]))
  const weight = modelLayers.value.length ? 1 / modelLayers.value.length : 0
  const layers: ColorSchemeItem[] = modelLayers.value.map(layer => {
    const firstTarget = resolveLayerTargets(layer)[0]
    const color =
      layerColors[layer.id] ||
      (firstTarget ? originalColors[targetKey(firstTarget)] : null) ||
      (firstTarget ? getDefaultColorFromMap(firstTarget) : null) ||
      layer.defaultColor ||
      '#808080'
    const prev = prevById.get(layer.id)
    const sem = prev?.semantic ?? semanticForLayerId(layer.id)
    const row: ColorSchemeItem = {
      id: layer.id,
      color: normalizeToHex(color) || '#808080',
      weight,
    }
    if (sem !== undefined) row.semantic = sem
    return row
  })

  return { layers }
}

function syncLayerColorsFromScheme(scheme: ColorScheme) {
  const configurable = new Set(modelLayers.value.map(l => l.id))
  const nextIds = new Set<string>()

  scheme.layers.forEach(item => {
    if (!configurable.has(item.id)) return
    const h = normalizeToHex(item.color)
    if (h) {
      layerColors[item.id] = h
      nextIds.add(item.id)
    }
  })

  Object.keys(layerColors).forEach(id => {
    if (configurable.has(id) && !nextIds.has(id)) {
      delete layerColors[id]
    }
  })
}

const updateColorSchemeInStore = () => {
  const map = getMap()
  if (!map || !map.isStyleLoaded()) {
    if (map) {
      map.once('load', () => {
        setTimeout(() => updateColorSchemeInStore(), 100)
      })
    }
    return
  }

  colorSchemeStore.setCurrentScheme(generateCurrentColorScheme())
}

watch(
  () => mapInstanceRef.value,
  mapInstance => {
    if (!mapInstance || typeof mapInstance.on !== 'function') return

    const initMap = () => {
      setTimeout(() => {
        saveOriginalColors()
        updateColorSchemeInStore()
      }, 500)
    }

    if (typeof mapInstance.isStyleLoaded === 'function' && mapInstance.isStyleLoaded()) {
      initMap()
    } else if (typeof mapInstance.once === 'function') {
      mapInstance.once('load', initMap)
    }
  },
  { immediate: true },
)

watch(
  () => colorSchemeStore.currentScheme.layers.map(l => `${l.id}:${l.color}`).join('|'),
  () => {
    syncLayerColorsFromScheme(colorSchemeStore.currentScheme)
    if (!getMap()?.isStyleLoaded()) return
    applyColorsToMap()
  },
)

watch(showLabelLayers, () => {
  updateColorSchemeInStore()
})

onMounted(() => {
  updateColorSchemeInStore()

  let checkCount = 0
  const checkMap = setInterval(() => {
    checkCount++
    const map = getMap()
    if (map?.isStyleLoaded()) {
      clearInterval(checkMap)
      saveOriginalColors()
      updateColorSchemeInStore()
    }
    if (checkCount > 100) {
      clearInterval(checkMap)
    }
  }, 200)
})
</script>

<style scoped>
.map-style {
  --studio-bg: #ffffff;
  --studio-bg-soft: #f6f8fb;
  --studio-border: #e5eaf1;
  --studio-text: #1f2937;
  --studio-text-muted: #667085;
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
  gap: 12px;
  padding: 12px 14px;
  border-bottom: 1px solid var(--studio-border);
  background: var(--studio-bg);
}

.style-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 650;
  letter-spacing: 0;
  color: var(--studio-text);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.style-content {
  flex: 1;
  overflow-y: auto;
}

.scheme-dialog-head h3 {
  margin: 0;
  color: #111827;
  font-size: 18px;
  font-weight: 700;
}

.scheme-dialog-head p {
  margin: 6px 0 0;
  color: #667085;
  font-size: 13px;
}

.scheme-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.mode-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.mode-card {
  padding: 14px;
  border: 1px solid #dbe3ee;
  border-radius: 10px;
  background: #f8fafc;
  text-align: left;
  cursor: pointer;
}

.mode-card strong {
  display: block;
  margin-bottom: 6px;
  color: #1f2937;
  font-size: 14px;
}

.mode-card span {
  color: #667085;
  font-size: 12px;
  line-height: 1.45;
}

.mode-card.active {
  border-color: #4264fb;
  background: #eef3ff;
  box-shadow: 0 0 0 3px rgba(66, 100, 251, 0.12);
}

.number-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.number-grid label {
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: #344054;
  font-size: 13px;
  font-weight: 600;
}

.semantic-editor {
  border: 1px solid #e5eaf1;
  border-radius: 10px;
  overflow: hidden;
}

.semantic-editor-head {
  padding: 12px 14px;
  background: #f8fafc;
  border-bottom: 1px solid #e5eaf1;
}

.semantic-editor-head strong {
  display: block;
  color: #1f2937;
  font-size: 14px;
}

.semantic-editor-head span {
  display: block;
  margin-top: 4px;
  color: #667085;
  font-size: 12px;
}

.semantic-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 150px;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-bottom: 1px solid #eef2f6;
  font-size: 13px;
  color: #344054;
}

.semantic-row:last-child {
  border-bottom: none;
}

.semantic-hint {
  margin: 0;
  padding: 10px 14px;
  color: #667085;
  font-size: 12px;
  line-height: 1.5;
  background: #fbfcfe;
}

.studio-collapse.category-section {
  border: none;
  --el-collapse-border-color: var(--studio-border);
}

.studio-collapse :deep(.el-collapse-item__header) {
  height: 40px;
  padding: 0 14px;
  font-weight: 650;
  font-size: 13px;
  color: var(--studio-text);
  background: var(--studio-bg);
  border-bottom: 1px solid var(--studio-border);
}

.studio-collapse :deep(.el-collapse-item__wrap),
.studio-collapse :deep(.el-collapse-item__content) {
  padding: 0;
  border-bottom: none;
  background: var(--studio-bg);
}

.layer-list {
  padding: 4px 0;
}

.studio-layer-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 7px 12px;
  min-height: 44px;
  border-bottom: 1px solid #eef2f6;
  background: var(--studio-bg);
}

.studio-layer-row:hover {
  background: var(--studio-bg-soft);
}

.studio-layer-main {
  display: grid;
  grid-template-columns: 32px minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.studio-color-chip {
  width: 30px;
  height: 20px;
  border-radius: 5px;
  border: 1px solid rgba(31, 41, 55, 0.16);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.35);
}

.studio-layer-name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  font-weight: 600;
  color: var(--studio-text);
}

.studio-hex {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  color: #475467;
  font-weight: 600;
  font-size: 11px;
  white-space: nowrap;
}

.studio-color-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.studio-reset-btn {
  width: 28px !important;
  height: 28px !important;
  padding: 0 !important;
  border-radius: 6px !important;
  color: var(--studio-text-muted) !important;
  font-size: 15px !important;
}

.studio-reset-btn:hover {
  color: var(--studio-text) !important;
  background: #edf1f7 !important;
}

:deep(.el-color-picker) {
  height: 28px;
}

:deep(.el-color-picker__trigger) {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 1px solid #d0d7e2;
  box-shadow: none;
}

.generate-section {
  padding: 14px 16px;
  border-top: 1px solid var(--studio-border);
  background: #fff;
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
  --el-button-border-color: #cbd5e1;
}
</style>
