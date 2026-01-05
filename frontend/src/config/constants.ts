/**
 * 应用常量配置
 */
export const MAP_CONFIG = {
  DEFAULT_CENTER: [116.3974, 39.9093] as [number, number], // 北京天安门
  DEFAULT_ZOOM: 10,
  MIN_ZOOM: 2,
  MAX_ZOOM: 22,
  SYNC_DELAY: 150, // 地图同步延迟（毫秒）
} as const

export const API_CONFIG = {
  TIMEOUT: 5000,
  DEBOUNCE_DELAY: 200,
  SEARCH_MIN_LENGTH: 2,
  SEARCH_RESULT_LIMIT: 5,
} as const

export const STORAGE_KEYS = {
  LOCALE: 'locale',
  MAP_STATE: 'mapState',
  COLOR_SCHEME: 'colorScheme',
} as const

export const IMAGE_CONFIG = {
  GRID_COLUMNS: 3,
  THUMBNAIL_WIDTH: 200,
  THUMBNAIL_HEIGHT: 150,
  FULL_WIDTH: 400,
  FULL_HEIGHT: 300,
} as const
