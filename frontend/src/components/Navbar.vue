<template>
  <div class="navbar">
    <div class="nav-left">
      <img class="logo" :src="logoImg" alt="PlaceMap Generator" />
    </div>

    <div class="nav-center">
      <h1 class="title">{{ t('navbar.title') }}</h1>
    </div>

    <div class="nav-right">
      <el-dropdown trigger="click" @command="handleLocaleChange" class="lang-select">
        <span class="dropdown-trigger">
          {{ currentLabel }}
          <el-icon><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="zh-CN">中文</el-dropdown-item>
            <el-dropdown-item command="en-US">English</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores'
import { ArrowDown } from '@element-plus/icons-vue'
import logoImg from '@/assets/logo.png'

const { locale, t } = useI18n()
const appStore = useAppStore()
const currentLocale = ref<string>(locale.value)
const currentLabel = computed(() => (currentLocale.value === 'zh-CN' ? '中文' : 'English'))

const handleLocaleChange = (value: string) => {
  if (value === 'zh-CN' || value === 'en-US') {
  appStore.setLocale(value)
  currentLocale.value = value
  }
}
</script>

<style scoped>
.navbar {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: #d6dbe0;
  gap: 16px;
  position: relative;
}

.nav-left {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo {
  height: 80px;
  width: auto;
  object-fit: contain;
}

.nav-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 4px;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.title {
  margin: 0;
  font-size: 1.5em;
  font-weight: 600;
  color: #1f2937;
}


.nav-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.lang-select {
  min-width: 140px;
}

.dropdown-trigger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  user-select: none;
}
</style>

