/**
 * Place search API service.
 *
 * The browser tries AMap first because the local Python backend may be unable
 * to reach restapi.amap.com in some network environments. The backend place
 * search remains as a fallback.
 */
import { API_CONFIG, getApiBaseUrl } from '@/config'
import type { GeocodeFeature } from '@/types/api'

const AMAP_TEXT_SEARCH_URL = 'https://restapi.amap.com/v3/place/text'
const backendUrl = () => getApiBaseUrl()

interface PlaceSearchResult {
  id: string
  name: string
  address?: string | null
  place_name: string
  center: [number, number]
  provider: 'amap' | 'nominatim'
  raw_center: [number, number]
  coordinate_system: 'WGS84' | 'GCJ02'
  type?: string | null
  confidence?: number | null
  properties?: Record<string, unknown>
}

interface AMapPoi {
  id?: string
  name?: string
  location?: string
  address?: string | unknown[]
  pname?: string
  cityname?: string
  adname?: string
  type?: string
  typecode?: string
}

interface AMapResponse {
  status?: string
  info?: string
  infocode?: string
  pois?: AMapPoi[]
}

const PI = Math.PI
const A = 6378245.0
const EE = 0.00669342162296594323

function transformLat(lng: number, lat: number): number {
  let ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + 0.1 * lng * lat
  ret += 0.2 * Math.sqrt(Math.abs(lng))
  ret += ((20.0 * Math.sin(6.0 * lng * PI) + 20.0 * Math.sin(2.0 * lng * PI)) * 2.0) / 3.0
  ret += ((20.0 * Math.sin(lat * PI) + 40.0 * Math.sin((lat / 3.0) * PI)) * 2.0) / 3.0
  ret += ((160.0 * Math.sin((lat / 12.0) * PI) + 320 * Math.sin((lat * PI) / 30.0)) * 2.0) / 3.0
  return ret
}

function transformLng(lng: number, lat: number): number {
  let ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + 0.1 * lng * lat
  ret += 0.1 * Math.sqrt(Math.abs(lng))
  ret += ((20.0 * Math.sin(6.0 * lng * PI) + 20.0 * Math.sin(2.0 * lng * PI)) * 2.0) / 3.0
  ret += ((20.0 * Math.sin(lng * PI) + 40.0 * Math.sin((lng / 3.0) * PI)) * 2.0) / 3.0
  ret += ((150.0 * Math.sin((lng / 12.0) * PI) + 300.0 * Math.sin((lng / 30.0) * PI)) * 2.0) / 3.0
  return ret
}

function outOfChina(lng: number, lat: number): boolean {
  return lng < 72.004 || lng > 137.8347 || lat < 0.8293 || lat > 55.8271
}

function gcj02ToWgs84(lng: number, lat: number): [number, number] {
  if (outOfChina(lng, lat)) return [lng, lat]
  let dlat = transformLat(lng - 105.0, lat - 35.0)
  let dlng = transformLng(lng - 105.0, lat - 35.0)
  const radlat = (lat / 180.0) * PI
  let magic = Math.sin(radlat)
  magic = 1 - EE * magic * magic
  const sqrtMagic = Math.sqrt(magic)
  dlat = (dlat * 180.0) / (((A * (1 - EE)) / (magic * sqrtMagic)) * PI)
  dlng = (dlng * 180.0) / ((A / sqrtMagic) * Math.cos(radlat) * PI)
  const mgLat = lat + dlat
  const mgLng = lng + dlng
  return [lng * 2 - mgLng, lat * 2 - mgLat]
}

function parseLngLat(value?: string): [number, number] | null {
  if (!value) return null
  const [lngText, latText] = value.split(',')
  const lng = Number(lngText)
  const lat = Number(latText)
  if (!Number.isFinite(lng) || !Number.isFinite(lat)) return null
  if (lng < -180 || lng > 180 || lat < -90 || lat > 90) return null
  return [lng, lat]
}

function joinNonEmpty(parts: Array<unknown>, sep = ''): string {
  return parts.map(part => String(part || '').trim()).filter(Boolean).join(sep)
}

function normalizePlaceResult(item: PlaceSearchResult): GeocodeFeature {
  const center = item.center
  return {
    id: item.id,
    type: 'Feature',
    place_type: item.type ? [item.type] : ['place'],
    relevance: item.confidence ?? 1,
    properties: {
      ...(item.properties || {}),
      provider: item.provider,
      raw_center: item.raw_center,
      coordinate_system: item.coordinate_system,
    },
    text: item.name,
    name: item.name,
    address: item.address,
    provider: item.provider,
    raw_center: item.raw_center,
    coordinate_system: item.coordinate_system,
    confidence: item.confidence,
    place_name: item.place_name,
    center,
    geometry: {
      type: 'Point',
      coordinates: center,
    },
  }
}

function normalizeAmapPoi(poi: AMapPoi, index: number, keyword: string): GeocodeFeature | null {
  const raw = parseLngLat(poi.location)
  if (!raw) return null

  const [rawLng, rawLat] = raw
  const center = gcj02ToWgs84(rawLng, rawLat)
  const name = String(poi.name || keyword).trim()
  const address = Array.isArray(poi.address) ? '' : String(poi.address || '').trim()
  const addressText = joinNonEmpty([poi.pname, poi.cityname, poi.adname, address])
  const placeName = joinNonEmpty([name, addressText], ' - ') || name
  const item: PlaceSearchResult = {
    id: `amap:${poi.id || index}`,
    name,
    address: addressText || null,
    place_name: placeName,
    center,
    provider: 'amap',
    raw_center: raw,
    coordinate_system: 'GCJ02',
    type: poi.type || poi.typecode || null,
    confidence: 0.95,
    properties: {
      city: poi.cityname,
      district: poi.adname,
      typecode: poi.typecode,
      source: 'browser',
    },
  }
  return normalizePlaceResult(item)
}

function fetchAmapJsonp(params: URLSearchParams, timeoutMs: number): Promise<AMapResponse> {
  return new Promise((resolve, reject) => {
    const callbackName = `__placemapAmap_${Date.now()}_${Math.random().toString(36).slice(2)}`
    const script = document.createElement('script')
    const timeoutId = window.setTimeout(() => {
      cleanup()
      reject(new Error('AMap JSONP timed out'))
    }, timeoutMs)

    function cleanup() {
      window.clearTimeout(timeoutId)
      script.remove()
      delete (window as any)[callbackName]
    }

    ;(window as any)[callbackName] = (payload: AMapResponse) => {
      cleanup()
      resolve(payload)
    }

    params.set('callback', callbackName)
    script.onerror = () => {
      cleanup()
      reject(new Error('AMap JSONP failed'))
    }
    script.src = `${AMAP_TEXT_SEARCH_URL}?${params.toString()}`
    document.head.appendChild(script)
  })
}

async function searchAmapInBrowser(query: string, limit: number): Promise<GeocodeFeature[]> {
  const key = (import.meta.env.VITE_AMAP_WEB_SERVICE_KEY as string | undefined)?.trim()
  if (!key) return []

  const params = new URLSearchParams({
    key,
    keywords: query.trim(),
    offset: limit.toString(),
    page: '1',
    extensions: 'base',
    output: 'json',
    citylimit: 'false',
  })

  let data: AMapResponse
  try {
    const controller = new AbortController()
    const timeoutId = window.setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT)
    const response = await fetch(`${AMAP_TEXT_SEARCH_URL}?${params.toString()}`, {
      method: 'GET',
      signal: controller.signal,
    })
    window.clearTimeout(timeoutId)
    data = await response.json()
  } catch {
    data = await fetchAmapJsonp(params, API_CONFIG.TIMEOUT)
  }

  if (String(data.status) !== '1') {
    console.warn('AMap search failed:', data.info || data.infocode)
    return []
  }

  return (data.pois || [])
    .map((poi, index) => normalizeAmapPoi(poi, index, query))
    .filter((item): item is GeocodeFeature => !!item)
}

async function searchBackend(query: string, limit: number): Promise<GeocodeFeature[]> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT)
  try {
    const params = new URLSearchParams({
      keyword: query.trim(),
      limit: limit.toString(),
      provider: 'auto',
    })

    const response = await fetch(`${backendUrl()}/api/places/search?${params.toString()}`, {
      method: 'GET',
      signal: controller.signal,
    })

    if (!response.ok) {
      throw new Error(`Place search API error: ${response.statusText}`)
    }

    const data: PlaceSearchResult[] = await response.json()
    return data.map(normalizePlaceResult)
  } finally {
    clearTimeout(timeoutId)
  }
}

export const geocodingApi = {
  search: async (
    query: string,
    limit = API_CONFIG.SEARCH_RESULT_LIMIT,
  ): Promise<GeocodeFeature[]> => {
    if (!query || query.trim().length < API_CONFIG.SEARCH_MIN_LENGTH) {
      return []
    }

    try {
      const amapResults = await searchAmapInBrowser(query, limit)
      if (amapResults.length > 0) return amapResults
    } catch (error) {
      console.warn('Browser AMap search failed, falling back to backend:', error)
    }

    try {
      return await searchBackend(query, limit)
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.error('Place search timed out')
      } else {
        console.error('Place search failed:', error)
      }
      return []
    }
  },
}
