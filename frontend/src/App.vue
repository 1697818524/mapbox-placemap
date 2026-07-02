<template>
  <div id="app">
    <el-config-provider :locale="elementLocale">
      <router-view />
    </el-config-provider>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import en from 'element-plus/dist/locale/en.mjs'
import { storeToRefs } from 'pinia'
import { useAppStore } from '@/stores'

const appStore = useAppStore()
const { locale } = storeToRefs(appStore)
const elementLocale = computed(() => (locale.value === 'zh-CN' ? zhCn : en))
</script>

<style scoped>
/* 组件样式 */
</style>
