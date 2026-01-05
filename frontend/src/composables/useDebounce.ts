/**
 * 防抖组合式函数
 */
import { ref, onBeforeUnmount } from 'vue'

export function useDebounce<T extends (...args: any[]) => any>(fn: T, delay: number = 200) {
  const timeoutId = ref<ReturnType<typeof setTimeout> | null>(null)

  const debouncedFn = (...args: Parameters<T>) => {
    if (timeoutId.value) {
      clearTimeout(timeoutId.value)
    }
    timeoutId.value = window.setTimeout(() => {
      fn(...args)
    }, delay)
  }

  const cancel = () => {
    if (timeoutId.value) {
      clearTimeout(timeoutId.value)
      timeoutId.value = null
    }
  }

  onBeforeUnmount(() => {
    cancel()
  })

  return {
    debouncedFn,
    cancel,
  }
}
