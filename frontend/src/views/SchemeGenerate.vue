<template>
  <div class="scheme-page">
    <div class="navbar">
      <Navbar />
    </div>
    <div class="main-content">
      <aside class="left-sidebar">
        <ObjectiveScoresPanel class="scores-block" />
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
                @click="onGenerateSchemes"
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
  </div>
</template>

<script setup lang="ts">
import { ref, provide, computed } from 'vue'
import type mapboxgl from 'mapbox-gl'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { storeToRefs } from 'pinia'
import Navbar from '@/components/Navbar.vue'
import MapDisplay from '@/components/MapDisplay.vue'
import MapStyle from '@/components/MapStyle.vue'
import ObjectiveScoresPanel from '@/components/ObjectiveScoresPanel.vue'
import { useColorSchemeStore } from '@/stores'
import { schemeApi } from '@/api/scheme'

const { t } = useI18n()

const mapInstanceRef = ref<mapboxgl.Map | null>(null)
provide('mapInstance', mapInstanceRef)

const colorSchemeStore = useColorSchemeStore()
const { currentScheme, lastPipelineJobId, schemeGenerationReady } = storeToRefs(colorSchemeStore)

const isGenerating = ref(false)
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

async function onGenerateSchemes() {
  if (!currentScheme.value.layers.length) {
    ElMessage.warning(t('mapStyle.noCurrentScheme'))
    return
  }
  if (!lastPipelineJobId.value || !schemeGenerationReady.value) {
    ElMessage.warning(t('mapStyle.generateBlockedNeedPipeline'))
    return
  }

  isGenerating.value = true
  try {
    const response = await schemeApi.generateSchemes({
      currentScheme: currentScheme.value,
      count: 5,
      jobId: lastPipelineJobId.value || undefined,
    })
    colorSchemeStore.setColorSchemes(response.schemes)
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
  height: 100px;
  background-color: #fefefe;
  flex-shrink: 0;
}

.main-content {
  display: flex;
  flex-grow: 1;
  flex-direction: row;
  overflow: hidden;
  min-height: 0;
  background-color: #e0cece;
}

.left-sidebar {
  width: 300px;
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
  background-color: #eec9c9;
}

.right-sidebar {
  width: 400px;
  flex-shrink: 0;
  background-color: #f0f0f0;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.studio-toolbar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: #eaeaea;
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
</style>
