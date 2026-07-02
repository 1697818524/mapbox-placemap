<template>
  <div class="scheme-page">
    <div class="navbar">
      <Navbar />
    </div>
    <div class="main-content">
      <aside class="left-sidebar">
        <ObjectiveScoresPanel
          class="scores-block"
          :generation-mode="semanticMode"
          :population="population"
          :generations="generations"
          :available-semantics="availableSemantics"
        />
      </aside>
      <div class="map-container">
        <MapDisplay />
      </div>
      <aside class="right-sidebar">
        <div class="studio-toolbar">
          <el-tooltip :content="regenerateBlockedReason" placement="top" :disabled="canGenerate">
            <span class="toolbar-btn-wrap">
              <el-button
                type="primary"
                size="small"
                :loading="isGenerating"
                :disabled="!canGenerate"
                @click="openGenerateDialog"
              >
                {{ isGenerating ? t('mapStyle.generating') : t('mapStyle.generateSchemes') }}
              </el-button>
            </span>
          </el-tooltip>
          <router-link class="toolbar-link" to="/">{{ t('generatePage.backHome') }}</router-link>
        </div>
        <MapStyle class="map-style-fill" footer-mode="gallery" />
      </aside>
    </div>

    <el-dialog v-model="dialogVisible" width="560px" :show-close="!isGenerating">
      <template #header>
        <div class="dialog-head">
          <h3>{{ t('schemeDialog.title') }}</h3>
          <p>{{ t('schemeDialog.description') }}</p>
        </div>
      </template>
      <div class="dialog-form">
        <div class="mode-row">
          <button type="button" class="mode-card" :class="{ active: semanticMode === 'local' }" @click="semanticMode = 'local'">
            <strong>{{ t('schemeDialog.localMode') }}</strong>
            <span>{{ t('schemeDialog.localDescription') }}</span>
          </button>
          <button type="button" class="mode-card" :class="{ active: semanticMode === 'global' }" @click="semanticMode = 'global'">
            <strong>{{ t('schemeDialog.globalMode') }}</strong>
            <span>{{ t('schemeDialog.globalDescription') }}</span>
          </button>
        </div>
        <div class="number-grid">
          <label>
            <span>{{ t('schemeDialog.population') }}</span>
            <el-input-number v-model="population" :min="8" :max="200" :step="4" size="small" />
          </label>
          <label>
            <span>{{ t('schemeDialog.generations') }}</span>
            <el-input-number v-model="generations" :min="1" :max="200" :step="5" size="small" />
          </label>
        </div>
        <div v-if="semanticMode === 'local'" class="semantic-list">
          <div v-for="layer in semanticSchemeLayers" :key="layer.id" class="semantic-row">
            <span>{{ layerName(layer.id) }}</span>
            <el-select v-model="layerSemantics[layer.id]" size="small">
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
        <el-button :disabled="isGenerating" @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-tooltip :content="localGenerateBlockedReason" placement="top" :disabled="!localGenerateBlocked">
          <span>
            <el-button
              type="primary"
              :loading="isGenerating"
              :disabled="localGenerateBlocked"
              @click="onGenerateSchemes"
            >
              {{ t('schemeDialog.start') }}
            </el-button>
          </span>
        </el-tooltip>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, provide, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { storeToRefs } from 'pinia'
import Navbar from '@/components/Navbar.vue'
import MapDisplay from '@/components/MapDisplay.vue'
import MapStyle from '@/components/MapStyle.vue'
import ObjectiveScoresPanel from '@/components/ObjectiveScoresPanel.vue'
import { useColorSchemeStore } from '@/stores'
import { schemeApi } from '@/api/scheme'
import { pipelineApi } from '@/api/pipeline'
import { MAP_SEMANTIC_OPTIONS, isMapSemanticValue } from '@/config/semanticOptions'
import type { MapboxMapInstance } from '@/composables'

const { t } = useI18n()

const mapInstanceRef = ref<MapboxMapInstance | null>(null)
provide('mapInstance', mapInstanceRef)

const colorSchemeStore = useColorSchemeStore()
const { currentScheme, lastPipelineJobId, schemeGenerationReady } = storeToRefs(colorSchemeStore)

const isGenerating = ref(false)
const dialogVisible = ref(false)
const semanticMode = ref<'local' | 'global'>('local')
const population = ref(40)
const generations = ref(25)
const availableSemantics = ref<string[]>([])
const layerSemantics = ref<Record<string, string>>({})
const semanticOptions = MAP_SEMANTIC_OPTIONS
const semanticOptionsWithState = computed(() => {
  const available = new Set(availableSemantics.value)
  return semanticOptions.map(option => ({
    ...option,
    disabled: available.size === 0 || !available.has(option.value),
  }))
})
const semanticSchemeLayers = computed(() =>
  currentScheme.value.layers.filter(layer => !!layer.semantic && layer.semantic !== 'base'),
)
const availableSemanticLabels = computed(() =>
  availableSemantics.value
    .map(value => (isMapSemanticValue(value) ? t(`mapStyle.semantics.${value}`) : value))
    .join(t('common.listSeparator')),
)
const missingLocalLayers = computed(() => {
  if (semanticMode.value !== 'local') return []
  if (availableSemantics.value.length === 0) return semanticSchemeLayers.value
  const available = new Set(availableSemantics.value)
  return semanticSchemeLayers.value.filter(layer => {
    const sem = layerSemantics.value[layer.id] || layer.semantic || 'green'
    return !available.has(sem)
  })
})
const localGenerateBlocked = computed(() => missingLocalLayers.value.length > 0 || isGenerating.value)
const localGenerateBlockedReason = computed(() => {
  if (isGenerating.value || !missingLocalLayers.value.length) return ''
  return t('schemeDialog.missingLocalLayers', {
    layers: missingLocalLayers.value.map(layer => layerName(layer.id)).join(t('common.listSeparator')),
  })
})
const canGenerate = computed(
  () =>
    currentScheme.value.layers.length > 0 &&
    !!lastPipelineJobId.value &&
    schemeGenerationReady.value,
)

const regenerateBlockedReason = computed(() => {
  if (currentScheme.value.layers.length === 0) return t('mapStyle.noCurrentScheme')
  if (!lastPipelineJobId.value) return t('mapStyle.generateBlockedNeedPipeline')
  if (!schemeGenerationReady.value) return t('mapStyle.generateBlockedNeedPipeline')
  return ''
})

function layerName(id: string): string {
  const nameKeys: Record<string, string> = {
    background: 'background',
    water: 'water',
    'road-level-1': 'roadLevel1',
    'road-level-2': 'roadLevel2',
    'road-level-3': 'roadLevel3',
    building: 'building',
    landuse: 'landuse',
  }
  const key = nameKeys[id]
  return key ? t(`mapStyle.layers.${key}`) : id
}

async function loadAvailableSemantics() {
  const jobId = lastPipelineJobId.value
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

async function openGenerateDialog() {
  if (!canGenerate.value) {
    ElMessage.warning(regenerateBlockedReason.value)
    return
  }
  semanticSchemeLayers.value.forEach(layer => {
    layerSemantics.value[layer.id] = layerSemantics.value[layer.id] || layer.semantic || 'green'
  })
  await loadAvailableSemantics()
  dialogVisible.value = true
}

function layerSemanticsPayload(): Record<string, string> {
  const semanticLayerIds = new Set(semanticSchemeLayers.value.map(layer => layer.id))
  return Object.fromEntries(
    Object.entries(layerSemantics.value).filter(
      ([layerId, semantic]) => semanticLayerIds.has(layerId) && !!semantic && semantic !== 'base',
    ),
  )
}

async function onGenerateSchemes() {
  if (!currentScheme.value.layers.length) {
    ElMessage.warning(t('mapStyle.noCurrentScheme'))
    return
  }
  if (!lastPipelineJobId.value || !schemeGenerationReady.value) {
    ElMessage.warning(t('mapStyle.generateBlockedNeedPipeline'))
    return
  }
  if (localGenerateBlocked.value) {
    ElMessage.warning(localGenerateBlockedReason.value)
    return
  }

  isGenerating.value = true
  try {
    const response = await schemeApi.generateSchemes({
      currentScheme: currentScheme.value,
      count: 5,
      jobId: lastPipelineJobId.value || undefined,
      population: population.value,
      generations: generations.value,
      semanticMode: semanticMode.value,
      layerSemantics: semanticMode.value === 'local' ? layerSemanticsPayload() : {},
    })
    colorSchemeStore.setColorSchemes(response.schemes)
    dialogVisible.value = false
    ElMessage.success(t('mapStyle.generateSuccess', { count: response.schemes.length }))
  } catch (error) {
    console.error(error)
    ElMessage.error(error instanceof Error ? error.message : t('mapStyle.generateError'))
  } finally {
    isGenerating.value = false
  }
}
</script>

<style scoped>
.scheme-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  min-height: 0;
  overflow: hidden;
  background: #fafbfc;
}

.navbar {
  height: 56px;
  background: #fafbfc;
  flex-shrink: 0;
  border-bottom: 1px solid #eceef2;
  position: relative;
  z-index: 10;
}

.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
  min-height: 0;
  background-color: #fafbfc;
}

.left-sidebar {
  width: 300px;
  flex-shrink: 0;
  padding: 16px;
  background-color: #fafbfc;
  overflow-y: auto;
  overscroll-behavior: contain;
}

.scores-block {
  min-height: 0;
}

.map-container {
  flex: 1;
  min-width: 0;
  background-color: #e8edf2;
}

.right-sidebar {
  width: 368px;
  flex-shrink: 0;
  background-color: #fff;
  display: flex;
  flex-direction: column;
  min-height: 0;
  border-left: 1px solid #eceef2;
}

.studio-toolbar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  background: #fff;
}

.toolbar-link {
  font-size: 13px;
  color: #5b6cf0;
  text-decoration: none;
  font-weight: 600;
}

.toolbar-link:hover {
  color: #4254d9;
}

.toolbar-btn-wrap {
  display: inline-block;
}

.map-style-fill {
  flex: 1;
  min-height: 0;
}

.dialog-head h3 {
  margin: 0;
  color: #1a1d23;
  font-size: 17px;
  font-weight: 700;
}

.dialog-head p {
  margin: 4px 0 0;
  color: #8b8f98;
  font-size: 13px;
}

.dialog-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.mode-row,
.number-grid {
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

.number-grid label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: #1a1d23;
  font-size: 13px;
  font-weight: 600;
}

.semantic-list {
  border: 1px solid #eceef2;
  border-radius: 10px;
  overflow: hidden;
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
</style>
