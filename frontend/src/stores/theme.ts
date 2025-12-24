import { defineStore } from 'pinia'
import { ref } from 'vue'

type ThemeMode = 'light' | 'dark'

export const useThemeStore = defineStore('theme', () => {
  const theme = ref<ThemeMode>('light')

  const setTheme = (mode: ThemeMode) => {
    theme.value = mode
    document.documentElement.setAttribute('data-theme', mode)
  }

  const toggleTheme = () => {
    setTheme(theme.value === 'light' ? 'dark' : 'light')
  }

  return {
    theme,
    setTheme,
    toggleTheme,
  }
})


