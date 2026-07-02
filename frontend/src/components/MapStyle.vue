<template>
  <div class="map-style">
    <div class="style-header">
      <h3>{{ t('mapStyle.title') }}</h3>
      <div class="header-actions">
        <el-button size="small" @click="resetAllColors">{{ t('mapStyle.resetAll') }}</el-button>
      </div>
      <input
        ref="styleImportInput"
        class="style-import-input"
        type="file"
        accept="application/json,.json"
        @change="handleImportStyle"
      />
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
                  {{ t('mapStyle.reset') }}
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
          <h3>{{ t('schemeDialog.title') }}</h3>
          <p>{{ t('schemeDialog.description') }}</p>
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
            <strong>{{ t('schemeDialog.localMode') }}</strong>
            <span>{{ t('schemeDialog.localDescription') }}</span>
          </button>
          <button
            type="button"
            class="mode-card"
            :class="{ active: schemeMode === 'global' }"
            @click="schemeMode = 'global'"
          >
            <strong>{{ t('schemeDialog.globalMode') }}</strong>
            <span>{{ t('schemeDialog.globalDescription') }}</span>
          </button>
        </div>

        <div class="number-grid">
          <label>
            <span>{{ t('schemeDialog.population') }}</span>
            <el-input-number v-model="schemePopulation" :min="8" :max="200" :step="4" size="small" />
          </label>
          <label>
            <span>{{ t('schemeDialog.generations') }}</span>
            <el-input-number v-model="schemeGenerations" :min="1" :max="200" :step="5" size="small" />
          </label>
        </div>

        <div v-if="schemeMode === 'local'" class="semantic-editor">
          <div class="semantic-editor-head">
            <strong>{{ t('schemeDialog.semanticMapping') }}</strong>
            <span>{{ t('schemeDialog.semanticMappingHint') }}</span>
          </div>
          <div v-for="layer in semanticEditableLayers" :key="layer.id" class="semantic-row">
            <span>{{ getLayerName(layer.nameKey) }}</span>
            <el-select v-model="layerSemanticDraft[layer.id]" size="small">
              <el-option
                v-for="option in semanticOptionsWithState"
                :key="option.value"
                :label="t(option.labelKey)"
                :value="option.value"
                :disabled="option.disabled"
              />
            </el-select>
          </div>
          <p v-if="availableSemantics.length" class="semantic-hint">
            {{ t('schemeDialog.availableSemantics', { values: availableSemanticLabels }) }}
          </p>
        </div>
      </div>

      <template #footer>
        <el-button :disabled="isGenerating" @click="schemeDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-tooltip :content="localGenerateBlockedReason" placement="top" :disabled="!localGenerateBlocked">
          <span>
            <el-button
              type="primary"
              :loading="isGenerating"
              :disabled="localGenerateBlocked"
              @click="confirmGenerateSchemes"
            >
              {{ isGenerating ? t('mapStyle.generating') : t('schemeDialog.start') }}
            </el-button>
          </span>
        </el-tooltip>
      </template>
    </el-dialog>

    <div class="style-file-actions">
      <span>{{ t('mapStyle.styleFile') }}</span>
      <div>
        <el-button size="small" @click="exportStyleConfig">{{ t('mapStyle.exportStyle') }}</el-button>
        <el-button size="small" @click="triggerImportStyle">{{ t('mapStyle.importStyle') }}</el-button>
      </div>
    </div>

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
  roadLevel1Layers,
  roadLevel2Layers,
  roadLevel3Layers,
  buildingLayers,
  greenLayers,
  getAllConfigurableLayers,
  getLayerTargets,
  type LayerConfig,
  type LayerTarget,
} from '@/config/mapStyleLayers'
import { MAP_SEMANTIC_OPTIONS, isMapSemanticValue } from '@/config/semanticOptions'
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
const { colorSchemes, selectedSchemeIndex, schemeGenerationReady, lastPipelineJobId } = storeToRefs(colorSchemeStore)
const getMap = (): MapboxMapInstance | null => mapInstanceRef.value
const isGalleryMode = computed(() => props.footerMode === 'gallery')

const activeCategories = ref<string[]>([
  'base',
  'water',
  'roadLevel1',
  'roadLevel2',
  'roadLevel3',
  'buildings',
  'green',
])
const layerColors = reactive<Record<string, string>>({})
const originalColors = reactive<Record<string, string>>({})
const styleImportInput = ref<HTMLInputElement | null>(null)

interface ExportedStyleLayer {
  id: string
  color: string
  semantic?: string
}

interface ExportedStyleConfig {
  version: 1
  exportedAt: string
  layers: ExportedStyleLayer[]
}

const styleCategories = computed(() => {
  const categories: Array<{ name: string; title: string; layers: LayerConfig[] }> = [
    { name: 'base', title: t('mapStyle.layers.background'), layers: baseLayers },
    {
      name: 'water',
      title: t('mapStyle.water'),
      layers: waterLayers,
    },
    { name: 'roadLevel1', title: t('mapStyle.layers.roadLevel1'), layers: roadLevel1Layers },
    {
      name: 'roadLevel2',
      title: t('mapStyle.layers.roadLevel2'),
      layers: roadLevel2Layers,
    },
    { name: 'roadLevel3', title: t('mapStyle.layers.roadLevel3'), layers: roadLevel3Layers },
    { name: 'buildings', title: t('mapStyle.buildings'), layers: buildingLayers },
    { name: 'green', title: t('mapStyle.green'), layers: greenLayers },
  ]

  return categories
})

const modelLayers = computed(() => getAllConfigurableLayers({ includeLabels: false }))
const allKnownLayers = computed(() => getAllConfigurableLayers({ includeLabels: false }))

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
const semanticOptions = MAP_SEMANTIC_OPTIONS
const semanticOptionsWithState = computed(() => {
  const available = new Set(availableSemantics.value)
  return semanticOptions.map(option => ({
    ...option,
    disabled: available.size === 0 || !available.has(option.value),
  }))
})
const semanticEditableLayers = computed(() => modelLayers.value.filter(layer => !!semanticForLayerId(layer.id)))
const availableSemanticLabels = computed(() =>
  availableSemantics.value
    .map(value => (isMapSemanticValue(value) ? t(`mapStyle.semantics.${value}`) : value))
    .join(t('common.listSeparator')),
)
const missingLocalLayers = computed(() => {
  if (schemeMode.value !== 'local') return []
  if (availableSemantics.value.length === 0) return semanticEditableLayers.value
  const available = new Set(availableSemantics.value)
  return semanticEditableLayers.value.filter(layer => {
    const sem = layerSemanticDraft[layer.id] || semanticForLayerId(layer.id) || 'green'
    return !available.has(sem)
  })
})
const localGenerateBlocked = computed(() => missingLocalLayers.value.length > 0 || isGenerating.value)
const localGenerateBlockedReason = computed(() => {
  if (isGenerating.value || !missingLocalLayers.value.length) return ''
  return t('schemeDialog.missingLocalLayers', {
    layers: missingLocalLayers.value.map(layer => getLayerName(layer.nameKey)).join(t('common.listSeparator')),
  })
})
const sampleSetReady = computed(() => schemeGenerationReady.value && !!lastPipelineJobId.value)
const canGenerate = computed(
  () => props.footerMode === 'generate' && colorSchemeStore.currentScheme.layers.length > 0 && sampleSetReady.value,
)
const generateBlockedReason = computed(() => {
  if (props.footerMode !== 'generate') return ''
  if (colorSchemeStore.currentScheme.layers.length === 0) return t('mapStyle.noCurrentScheme')
  if (!sampleSetReady.value) return t('mapStyle.generateBlockedNeedPipeline')
  return ''
})

function galleryPrev() {
  colorSchemeStore.setSelectedSchemeIndex(selectedSchemeIndex.value - 1)
}

function galleryNext() {
  colorSchemeStore.setSelectedSchemeIndex(selectedSchemeIndex.value + 1)
}

function syncSemanticDraft() {
  semanticEditableLayers.value.forEach(layer => {
    layerSemanticDraft[layer.id] = layerSemanticDraft[layer.id] || semanticForLayerId(layer.id) || 'green'
  })
}

function semanticLayerDraftPayload(): Record<string, string> {
  const payload: Record<string, string> = {}
  semanticEditableLayers.value.forEach(layer => {
    const semantic = layerSemanticDraft[layer.id]
    if (semantic && semantic !== 'base') {
      payload[layer.id] = semantic
    }
  })
  return payload
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
  if (localGenerateBlocked.value) {
    ElMessage.warning(localGenerateBlockedReason.value)
    return
  }
  isGenerating.value = true
  try {
    if (!sampleSetReady.value) {
      ElMessage.warning(t('mapStyle.generateBlockedNeedPipeline'))
      return
    }

    const response = await schemeApi.generateSchemes({
      currentScheme,
      count: 5,
      jobId: colorSchemeStore.lastPipelineJobId || undefined,
      population: schemePopulation.value,
      generations: schemeGenerations.value,
      semanticMode: schemeMode.value,
      layerSemantics: schemeMode.value === 'local' ? semanticLayerDraftPayload() : {},
    })
    colorSchemeStore.setColorSchemes(response.schemes)
    ElMessage.success(t('mapStyle.generateSuccess', { count: response.schemes.length }))
    schemeDialogVisible.value = false
    await router.push('/generate')
  } catch (error) {
    console.error('Failed to generate schemes:', error)
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

const shouldHidePoiLayer = (layerId: string): boolean => {
  const lower = layerId.toLowerCase()
  return [
    'poi',
    'transit',
    'station',
    'airport',
    'parking',
    'medical',
    'school',
    'shop',
    'restaurant',
    'commercial',
  ].some(token => lower.includes(token))
}

const applyMapLabelVisibility = () => {
  const map = getMap()
  if (!map || !map.isStyleLoaded()) return

  mapStyleLayers().forEach(styleLayer => {
    try {
      if (styleLayer.type === 'symbol' && shouldHidePoiLayer(styleLayer.id)) {
        map.setLayoutProperty(styleLayer.id, 'visibility', 'none')
      }
    } catch (error) {
      void error
    }
  })
}

const resolveLayerTargets = (layer: LayerConfig): LayerTarget[] => {
  const explicit = getLayerTargets(layer)
  const dynamic: LayerTarget[] = []

  mapStyleLayers().forEach(styleLayer => {
    const id = styleLayer.id
    const lower = id.toLowerCase()
    const type = styleLayer.type
    const isLabel = lower.includes('label') || lower.includes('symbol')
    const isRoadLine =
      type === 'line' &&
      !isLabel &&
      [
        'road',
        'street',
        'motorway',
        'trunk',
        'primary',
        'secondary',
        'tertiary',
        'minor',
        'path',
        'pedestrian',
        'service',
        'step',
        'bridge',
        'tunnel',
      ].some(token => lower.includes(token))

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
  applyMapLabelVisibility()
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

const exportStyleConfig = () => {
  const scheme = generateCurrentColorScheme()
  const payload: ExportedStyleConfig = {
    version: 1,
    exportedAt: new Date().toISOString(),
    layers: scheme.layers.map(layer => ({
      id: layer.id,
      color: layer.color,
      ...(layer.semantic ? { semantic: layer.semantic } : {}),
    })),
  }
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `placemap-style-${new Date().toISOString().slice(0, 10)}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}

const triggerImportStyle = () => {
  styleImportInput.value?.click()
}

const isStyleLayer = (value: unknown): value is ExportedStyleLayer => {
  if (!value || typeof value !== 'object') return false
  const row = value as Record<string, unknown>
  return typeof row.id === 'string' && typeof row.color === 'string' && !!normalizeToHex(row.color)
}

const applyImportedStyle = (payload: unknown) => {
  const raw = payload as Partial<ExportedStyleConfig>
  if (!raw || !Array.isArray(raw.layers)) {
    throw new Error(t('mapStyle.importInvalid'))
  }
  const layerById = new Map(modelLayers.value.map(layer => [layer.id, layer]))
  let applied = 0
  raw.layers.forEach(item => {
    if (!isStyleLayer(item)) return
    const layer = layerById.get(item.id)
    const color = normalizeToHex(item.color)
    if (!layer || !color) return
    layerColors[layer.id] = color
    resolveLayerTargets(layer).forEach(target => setTargetColor(target, color))
    if (item.semantic && item.semantic !== 'base') {
      layerSemanticDraft[layer.id] = item.semantic
    }
    applied += 1
  })
  if (!applied) {
    throw new Error(t('mapStyle.importNoLayers'))
  }
  updateColorSchemeInStore()
}

const handleImportStyle = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  try {
    const text = await file.text()
    applyImportedStyle(JSON.parse(text))
    ElMessage.success(t('mapStyle.importSuccess'))
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : t('mapStyle.importFailed'))
  }
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

const hslToHex = (hsl: string): string | null => {
  const match = hsl.match(/hsla?\(([-\d.]+),\s*([-\d.]+)%?,\s*([-\d.]+)%?/)
  if (!match) return null
  let h = Number(match[1])
  let s = Number(match[2]) / 100
  let l = Number(match[3]) / 100
  if (!Number.isFinite(h) || !Number.isFinite(s) || !Number.isFinite(l)) return null
  h = ((h % 360) + 360) % 360
  s = Math.min(Math.max(s, 0), 1)
  l = Math.min(Math.max(l, 0), 1)

  const c = (1 - Math.abs(2 * l - 1)) * s
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1))
  const m = l - c / 2
  const [r1, g1, b1] =
    h < 60 ? [c, x, 0] :
    h < 120 ? [x, c, 0] :
    h < 180 ? [0, c, x] :
    h < 240 ? [0, x, c] :
    h < 300 ? [x, 0, c] :
    [c, 0, x]
  const toHex = (n: number) => Math.round((n + m) * 255).toString(16).padStart(2, '0')
  return `#${toHex(r1)}${toHex(g1)}${toHex(b1)}`.toUpperCase()
}

const normalizeToHex = (color: string): string | null => {
  if (!color) return null
  const trimmed = color.trim()
  if (trimmed.startsWith('#')) {
    const hex = trimmed.replace('#', '')
    return /^[0-9A-Fa-f]{3}$/.test(hex) || /^[0-9A-Fa-f]{6}$/.test(hex)
      ? trimmed.toUpperCase()
      : null
  }
  if (trimmed.startsWith('rgb')) return rgbToHex(trimmed)
  if (trimmed.startsWith('hsl')) return hslToHex(trimmed)
  if (/^[0-9A-Fa-f]{3}$/.test(trimmed) || /^[0-9A-Fa-f]{6}$/.test(trimmed)) {
    return `#${trimmed.toUpperCase()}`
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

const initializeMapStyleState = () => {
  applyMapLabelVisibility()
  saveOriginalColors()
  if (isGalleryMode.value && colorSchemeStore.currentScheme.layers.length > 0) {
    syncLayerColorsFromScheme(colorSchemeStore.currentScheme)
    applyColorsToMap()
  } else {
    updateColorSchemeInStore()
  }
}

watch(
  () => mapInstanceRef.value,
  mapInstance => {
    if (!mapInstance || typeof mapInstance.on !== 'function') return

    const initMap = () => {
      setTimeout(() => {
        initializeMapStyleState()
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
    applyColorsToMap()
  },
  { immediate: true },
)

onMounted(() => {
  if (!isGalleryMode.value) {
    updateColorSchemeInStore()
  }

  let checkCount = 0
  const checkMap = setInterval(() => {
    checkCount++
    const map = getMap()
    if (map?.isStyleLoaded()) {
      clearInterval(checkMap)
      initializeMapStyleState()
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
  --studio-bg-soft: #f4f5f7;
  --studio-border: #eceef2;
  --studio-text: #1a1d23;
  --studio-text-muted: #8b8f98;
  --studio-accent: #5b6cf0;

  height: 100%;
  min-height: 0;
  overflow: hidden;
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
  min-height: 44px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--studio-border);
  background: var(--studio-bg);
}

.style-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0;
  color: var(--studio-text);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.style-import-input {
  display: none;
}

.style-content {
  flex: 1 1 0;
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
  background: #fff;
}

.scheme-dialog-head h3 {
  margin: 0;
  color: #1a1d23;
  font-size: 17px;
  font-weight: 700;
}

.scheme-dialog-head p {
  margin: 4px 0 0;
  color: #8b8f98;
  font-size: 13px;
}

.scheme-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.mode-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.mode-card {
  padding: 12px 14px;
  border: 1px solid #e2e5ea;
  border-radius: 10px;
  background: #fff;
  text-align: left;
  cursor: pointer;
  transition: border-color .15s, box-shadow .15s;
}

.mode-card:hover {
  border-color: #c5c9d2;
}

.mode-card strong {
  display: block;
  margin-bottom: 4px;
  color: #1a1d23;
  font-size: 13px;
}

.mode-card span {
  color: #8b8f98;
  font-size: 12px;
  line-height: 1.45;
}

.mode-card.active {
  border-color: #5b6cf0;
  background: #f5f7ff;
  box-shadow: 0 0 0 2px rgba(91, 108, 240, 0.1);
}

.number-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.number-grid label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: #1a1d23;
  font-size: 13px;
  font-weight: 600;
}

.semantic-editor {
  border: 1px solid #eceef2;
  border-radius: 10px;
  overflow: hidden;
}

.semantic-editor-head {
  padding: 10px 14px;
  background: #fafbfc;
  border-bottom: 1px solid #eceef2;
}

.semantic-editor-head strong {
  display: block;
  color: #1a1d23;
  font-size: 13px;
}

.semantic-editor-head span {
  display: block;
  margin-top: 3px;
  color: #8b8f98;
  font-size: 12px;
}

.semantic-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 140px;
  align-items: center;
  gap: 12px;
  padding: 9px 14px;
  border-bottom: 1px solid #f3f4f6;
  font-size: 13px;
  color: #1a1d23;
}

.semantic-row:last-child {
  border-bottom: none;
}

.semantic-hint {
  margin: 0;
  padding: 8px 14px;
  color: #8b8f98;
  font-size: 12px;
  line-height: 1.5;
  background: #fafbfc;
}

.studio-collapse.category-section {
  border: none;
  --el-collapse-border-color: var(--studio-border);
}

.studio-collapse :deep(.el-collapse-item__header) {
  height: 36px;
  padding: 0 16px;
  font-weight: 700;
  font-size: 13px;
  color: var(--studio-text);
  background: var(--studio-bg);
  border-bottom: 1px solid var(--studio-border);
}

.studio-collapse :deep(.el-collapse-item__wrap),
.studio-collapse :deep(.el-collapse-item__content) {
  padding: 0;
  border-bottom: none;
  background: #fafbfc;
}

.layer-list {
  padding: 4px 0;
}

.studio-layer-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 6px 16px;
  min-height: 40px;
  border-bottom: 1px solid #f3f4f6;
  background: transparent;
}

.studio-layer-row:hover {
  background: #f4f5f7;
}

.studio-layer-main {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.studio-color-chip {
  width: 26px;
  height: 18px;
  border-radius: 4px;
  border: 1px solid rgba(0, 0, 0, 0.1);
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
  color: #6b6f78;
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
  padding: 0 8px !important;
  height: 28px !important;
  border-radius: 6px !important;
  color: var(--studio-text-muted) !important;
  font-size: 12px !important;
  font-weight: 600 !important;
}

.studio-reset-btn:hover {
  color: var(--studio-text) !important;
  background: #eceef2 !important;
}

:deep(.el-color-picker) {
  height: 28px;
}

:deep(.el-color-picker__trigger) {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 1px solid #dde0e5;
  box-shadow: none;
}

.generate-section {
  padding: 12px 16px;
  border-top: 1px solid var(--studio-border);
  background: #fafbfc;
}

.style-file-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 9px 16px;
  border-top: 1px solid var(--studio-border);
  background: #fafbfc;
}

.style-file-actions span {
  font-size: 12px;
  font-weight: 600;
  color: var(--studio-text-muted);
}

.style-file-actions > div {
  display: flex;
  align-items: center;
  gap: 8px;
}

.style-file-actions :deep(.el-button) {
  --el-button-bg-color: #fff;
  --el-button-border-color: #dde0e5;
  --el-button-text-color: var(--studio-text);
  font-size: 11px;
}

.generate-btn-wrap {
  display: block;
  width: 100%;
}

.generate-button {
  width: 100%;
  height: 36px;
  font-size: 13px;
  font-weight: 700;
  border-radius: 8px;
  --el-button-bg-color: var(--studio-accent);
  --el-button-border-color: var(--studio-accent);
  --el-button-hover-bg-color: #4254d9;
  --el-button-hover-border-color: #4254d9;
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
  --el-button-border-color: #dde0e5;
  --el-button-text-color: var(--studio-text-muted);
  font-size: 11px;
}

.style-header :deep(.el-button:hover) {
  --el-button-text-color: var(--studio-text);
  --el-button-border-color: #c5c9d2;
}

.gallery-footer .gallery-hint {
  margin: 0;
  font-size: 12px;
  color: var(--studio-text-muted);
  text-align: center;
  line-height: 1.45;
}
</style>
