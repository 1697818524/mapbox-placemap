import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh-CN'
import enUS from './locales/en-US'

const i18n = createI18n({
  legacy: false,
  locale: localStorage.getItem('locale') || 'zh-CN',
  fallbackLocale: 'zh-CN',
  silentTranslationWarn: true, // 禁用翻译警告
  silentFallbackWarn: true, // 禁用回退警告
  missingWarn: false, // 禁用缺失键警告
  fallbackWarn: false, // 禁用回退警告
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS,
  },
})

export default i18n
