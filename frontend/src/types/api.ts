/**
 * API 相关类型定义
 */

/**
 * Mapbox Geocoding API 响应类型
 */
export interface GeocodeResponse {
  type: string
  query: string[]
  features: GeocodeFeature[]
  attribution: string
}

/**
 * Mapbox Geocoding 特征类型
 */
export interface GeocodeFeature {
  id: string
  type: string
  place_type: string[]
  relevance: number
  properties: {
    accuracy?: string
    [key: string]: any
  }
  text: string
  place_name: string
  center: [number, number] // [lng, lat]
  geometry: {
    type: string
    coordinates: [number, number]
  }
  context?: Array<{
    id: string
    text: string
    [key: string]: any
  }>
}

/**
 * 图片搜索结果类型
 */
export interface ImageResult {
  url: string
  thumbnail?: string
  title?: string
  width?: number
  height?: number
}
