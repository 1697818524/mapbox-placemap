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
          <h3>生成方案参数</h3>
          <p>调整遗传搜索参数和候选色使用方式。</p>
        </div>
      </template>
      <div class="dialog-form">
        <div class="mode-row">
          <button type="button" class="mode-card" :class="{ active: semanticMode === 'local' }" @click="semanticMode = 'local'">
            <strong>局部候选</strong>
            <span>样式使用对应语义；缺少候选时可临时改派。</span>
          </button>
          <button type="button" class="mode-card" :class="{ active: semanticMode === 'global' }" @click="semanticMode = 'global'">
            <strong>全局候选</strong>
            <span>每个样式可使用所有语义候选色。</span>
          </button>
        </div>
        <div class="number-grid">
          <label>
            <span>种群数</span>
            <el-input-number v-model="population" :min="8" :max="200" :step="4" size="small" />
          </label>
          <label>
            <span>迭代次数</span>
            <el-input-number v-model="generations" :min="1" :max="200" :step="5" size="small" />
          </label>
        </div>
        <div v-if="semanticMode === 'local'" class="semantic-list">
          <div v-for="layer in currentScheme.layers" :key="layer.id" class="semantic-row">
            <span>{{ layerName(layer.id) }}</span>
            <el-select v-model="layerSemantics[layer.id]" size="small">
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
        <el-button :disabled="isGenerating" @click="dialogVisible = false">取消</el-button>
        <el-tooltip :content="localGenerateBlockedReason" placement="top" :disabled="!localGenerateBlocked">
          <span>
            <el-button
              type="primary"
              :loading="isGenerating"
              :disabled="localGenerateBlocked"
              @click="onGenerateSchemes"
            >
              开始生成
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
    disabled: available.size === 0 || !available.has(option.value),
  }))
})
const missingLocalLayers = computed(() => {
  if (semanticMode.value !== 'local') return []
  if (availableSemantics.value.length === 0) return currentScheme.value.layers
  const available = new Set(availableSemantics.value)
  return currentScheme.value.layers.filter(layer => {
    const sem = layerSemantics.value[layer.id] || layer.semantic || 'green'
    return !available.has(sem)
  })
})
const localGenerateBlocked = computed(() => missingLocalLayers.value.length > 0 || isGenerating.value)
const localGenerateBlockedReason = computed(() => {
  if (isGenerating.value || !missingLocalLayers.value.length) return ''
  return `局部模式下这些样式缺少候选语义：${missingLocalLayers.value.map(layer => layerName(layer.id)).join('、')}。请改选可用语义。`
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
  const names: Record<string, string> = {
    background: '背景',
    water: '水体',
    'road-level-1': '一级道路',
    'road-level-2': '二级道路',
    'road-level-3': '三级道路',
    building: '建筑物',
    landuse: '土地利用',
  }
  return names[id] || id
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
  currentScheme.value.layers.forEach(layer => {
    layerSemantics.value[layer.id] = layerSemantics.value[layer.id] || layer.semantic || 'green'
  })
  await loadAvailableSemantics()
  dialogVisible.value = true
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
      layerSemantics: semanticMode.value === 'local' ? layerSemantics.value : {},
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
  height: 100%;
  min-height: 0;
}

.navbar {
  height: 88px;
  background-color: #fff;
  flex-shrink: 0;
  border-bottom: 1px solid #e7eaf0;
}

.main-content {
  display: flex;
  flex-grow: 1;
  flex-direction: row;
  overflow: hidden;
  min-height: 0;
  background-color: #f4f6f8;
}

.left-sidebar {
  width: 316px;
  flex-shrink: 0;
  padding: 12px;
  background-color: #fff;
  border-right: 1px solid #e4e7ed;
  overflow-y: auto;
}

.scores-block {
  min-height: 0;
}

.map-container {
  flex-grow: 1;
  min-width: 0;
  background-color: #edf1f5;
}

.right-sidebar {
  width: 392px;
  flex-shrink: 0;
  background-color: #fff;
  display: flex;
  flex-direction: column;
  min-height: 0;
  border-left: 1px solid #e4e7ed;
}

.studio-toolbar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: #fff;
  border-bottom: 1px solid #dcdfe6;
}

.toolbar-link {
  font-size: 13px;
  color: #4264fb;
  text-decoration: none;
  font-weight: 500;
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
  color: #111827;
  font-size: 18px;
  font-weight: 700;
}

.dialog-head p {
  margin: 6px 0 0;
  color: #667085;
  font-size: 13px;
}

.dialog-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.mode-row,
.number-grid {
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

.number-grid label {
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: #344054;
  font-size: 13px;
  font-weight: 600;
}

.semantic-list {
  border: 1px solid #e5eaf1;
  border-radius: 10px;
  overflow: hidden;
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
</style>
