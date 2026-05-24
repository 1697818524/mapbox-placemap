<template>
  <div class="scores-panel">
    <h3 class="title">{{ t('generatePage.scoresTitle') }}</h3>
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

const { t } = useI18n()
const store = useColorSchemeStore()
const { colorSchemes, selectedSchemeIndex } = storeToRefs(store)

const activeScheme = computed(() => {
  const list = colorSchemes.value
  const i = selectedSchemeIndex.value
  if (!list.length || i < 0 || i >= list.length) return null
  return list[i] as ColorSchemeWithId
})

const hasActiveScheme = computed(() => !!activeScheme.value)
const schemeId = computed(() => activeScheme.value?.id ?? '')

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
  if (Number.isNaN(v)) return '—'
  return (Math.round(v * 1000) / 1000).toFixed(3)
}
</script>

<style scoped>
.scores-panel {
  padding: 12px 14px;
  background: #fafafa;
  border: 1px solid #ebeef5;
  border-radius: 8px;
}

.title {
  margin: 0 0 10px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.placeholder {
  margin: 0;
  font-size: 12px;
  color: #909399;
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
  color: #606266;
}

.score-grid dd {
  margin: 0;
  font-family: ui-monospace, monospace;
  font-weight: 600;
  color: #303133;
  text-align: right;
}

.scheme-id {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid #ebeef5;
  font-size: 11px;
}

.scheme-id .label {
  color: #909399;
  margin-right: 6px;
}

.scheme-id code {
  word-break: break-all;
  font-size: 11px;
  background: #f0f2f5;
  padding: 2px 6px;
  border-radius: 4px;
}
</style>
