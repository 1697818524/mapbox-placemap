<template>
  <div class="navbar">
    <div class="nav-left">
      <img class="logo" :src="logoImg" alt="PlaceMap Generator" />
      <nav class="nav-links">
        <router-link to="/" class="nav-link">{{ t('nav.home') }}</router-link>
      </nav>
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
  padding: 0 20px;
  background: #fafbfc;
  gap: 20px;
  position: relative;
  border-bottom: 1px solid #eceef2;
}

.nav-left {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 14px;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 4px;
}

.nav-link {
  padding: 6px 12px;
  font-size: 13px;
  font-weight: 600;
  color: #6b6f78;
  text-decoration: none;
  border-radius: 8px;
  transition: color .15s, background .15s;
}

.nav-link:hover {
  color: #1a1d23;
  background: #eceef2;
}

.nav-link.router-link-active {
  color: #5b6cf0;
  background: rgba(91, 108, 240, 0.08);
}

.logo {
  height: 48px;
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
  font-size: 18px;
  font-weight: 700;
  color: #1a1d23;
}

.dropdown-trigger {
  font-size: 13px;
  color: #6b6f78;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 8px;
  border-radius: 8px;
  transition: background .15s;
}

.dropdown-trigger:hover {
  background: #eceef2;
}

.nav-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.lang-select {
  min-width: 88px;
}

.dropdown-trigger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  user-select: none;
  color: #475467;
  font-size: 13px;
  font-weight: 500;
}
</style>
