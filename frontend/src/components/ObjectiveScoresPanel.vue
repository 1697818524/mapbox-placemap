<template>
  <div class="scores-panel">
    <h3 class="title">{{ t('generatePage.scoresTitle') }}</h3>
    <section class="info-section">
      <div class="section-title">{{ t('objectivePanel.optimizationGoals') }}</div>
      <div class="objective-item">
        <strong>{{ t('objectivePanel.harmonyTitle') }}</strong>
        <span>{{ t('objectivePanel.harmonyDescription') }}</span>
      </div>
      <div class="objective-item">
        <strong>{{ t('objectivePanel.placeTitle') }}</strong>
        <span>{{ t('objectivePanel.placeDescription') }}</span>
      </div>
    </section>
    <section class="info-section">
      <div class="section-title">{{ t('objectivePanel.generationParams') }}</div>
      <dl class="score-grid">
        <dt>{{ t('objectivePanel.currentScheme') }}</dt>
        <dd>{{ schemePosition }}</dd>
        <dt>{{ t('objectivePanel.candidateMode') }}</dt>
        <dd>{{ modeLabel }}</dd>
        <dt>{{ t('schemeDialog.population') }}</dt>
        <dd>{{ population }}</dd>
        <dt>{{ t('schemeDialog.generations') }}</dt>
        <dd>{{ generations }}</dd>
        <dt>{{ t('objectivePanel.activeLayers') }}</dt>
        <dd>{{ activeLayerCount }}</dd>
        <dt>{{ t('objectivePanel.candidateSemantics') }}</dt>
        <dd class="clip-value">{{ candidateSemanticsText }}</dd>
        <dt>{{ t('objectivePanel.jobStatus') }}</dt>
        <dd>{{ jobStatusText }}</dd>
      </dl>
    </section>
    <p v-if="!hasActiveScheme" class="placeholder">{{ t('generatePage.scoresNoScheme') }}</p>
    <template v-else-if="hasScores">
      <dl class="score-grid">
        <template v-if="scores!.harmony != null">
          <dt>{{ t('generatePage.scoreHarmony') }}</dt>
          <dd>{{ formatScore(scores!.harmony) }}</dd>
        </template>
        <template v-if="scores!.place_representativeness != null">
          <dt>{{ t('generatePage.scorePlace') }}</dt>
          <dd>{{ formatScore(scores!.place_representativeness) }}</dd>
        </template>
        <dt>{{ t('generatePage.scoreSemanticFit') }}</dt>
        <dd>{{ formatScore(scores!.semantic_fit ?? 0) }}</dd>
        <dt>{{ t('generatePage.scoreReadability') }}</dt>
        <dd>{{ formatScore(scores!.readability ?? 0) }}</dd>
        <dt>{{ t('generatePage.scoreDiversity') }}</dt>
        <dd>{{ formatScore(scores!.diversity ?? 0) }}</dd>
      </dl>
    </template>
    <p v-else class="placeholder">{{ t('generatePage.scoresNoMetrics') }}</p>
    <div class="scheme-id" v-if="schemeId">
      <span class="label">{{ t('generatePage.schemeId') }}</span>
      <code>{{ schemeId }}</code>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useI18n } from 'vue-i18n'
import { useColorSchemeStore, type ColorSchemeWithId, type SchemeScores } from '@/stores'
import { isMapSemanticValue } from '@/config/semanticOptions'

const props = withDefaults(
  defineProps<{
    generationMode?: 'local' | 'global'
    population?: number
    generations?: number
    availableSemantics?: string[]
  }>(),
  {
    generationMode: 'local',
    population: 40,
    generations: 25,
    availableSemantics: () => [],
  },
)

const { t } = useI18n()
const store = useColorSchemeStore()
const { colorSchemes, selectedSchemeIndex, currentScheme, lastPipelineJobId, schemeGenerationReady } = storeToRefs(store)

const activeScheme = computed(() => {
  const list = colorSchemes.value
  const i = selectedSchemeIndex.value
  if (!list.length || i < 0 || i >= list.length) return null
  return list[i] as ColorSchemeWithId
})

const hasActiveScheme = computed(() => !!activeScheme.value)
const schemeId = computed(() => activeScheme.value?.id ?? '')
const schemePosition = computed(() => {
  const total = colorSchemes.value.length
  if (!total) return '0 / 0'
  return `${selectedSchemeIndex.value + 1} / ${total}`
})
const modeLabel = computed(() =>
  props.generationMode === 'global' ? t('schemeDialog.globalMode') : t('schemeDialog.localMode'),
)
const activeLayerCount = computed(() => currentScheme.value.layers.length || activeScheme.value?.layers.length || 0)
const candidateSemanticsText = computed(() => {
  const values = props.availableSemantics
  if (!values.length) return t('objectivePanel.notRead')
  return values
    .map(value => (isMapSemanticValue(value) ? t(`mapStyle.semantics.${value}`) : value))
    .join(t('common.listSeparator'))
})
const jobStatusText = computed(() => {
  if (!lastPipelineJobId.value) return t('objectivePanel.noJob')
  return schemeGenerationReady.value ? t('objectivePanel.ready') : t('objectivePanel.notReady')
})

const scores = computed<SchemeScores | null>(() => {
  const s = activeScheme.value
  if (!s?.scores) return null
  return s.scores
})

const hasScores = computed(() => {
  const sc = scores.value
  if (!sc) return false
  return (
    sc.harmony != null ||
    sc.place_representativeness != null ||
    sc.semantic_fit != null ||
    sc.readability != null ||
    sc.diversity != null
  )
})

function formatScore(v: number): string {
  if (Number.isNaN(v)) return t('common.empty')
  return (Math.round(v * 1000) / 1000).toFixed(3)
}
</script>

<style scoped>
.scores-panel {
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 0;
}

.title {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 700;
  color: #1a1d23;
}

.info-section {
  padding: 12px 0;
  border-top: 1px solid #eceef2;
}

.title + .info-section {
  border-top: none;
  padding-top: 0;
}

.section-title {
  margin-bottom: 8px;
  color: #6b6f78;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.objective-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #f3f4f6;
}

.objective-item + .objective-item {
  margin-top: 6px;
}

.objective-item strong {
  color: #1a1d23;
  font-size: 12px;
}

.objective-item span {
  color: #8b8f98;
  font-size: 11px;
  line-height: 1.45;
}

.placeholder {
  margin: 0;
  font-size: 12px;
  color: #8b8f98;
  line-height: 1.5;
}

.score-grid {
  margin: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 6px 12px;
  font-size: 12px;
}

.score-grid dt {
  margin: 0;
  color: #8b8f98;
}

.score-grid dd {
  margin: 0;
  font-family: ui-monospace, 'Cascadia Code', 'Source Code Pro', monospace;
  font-weight: 700;
  color: #1a1d23;
  text-align: right;
}

.clip-value {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.scheme-id {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid #eceef2;
  font-size: 11px;
}

.scheme-id .label {
  color: #8b8f98;
  margin-right: 6px;
}

.scheme-id code {
  display: block;
  margin-top: 4px;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 11px;
  background: #f3f4f6;
  padding: 4px 8px;
  border-radius: 6px;
  color: #6b6f78;
}
</style>
