/**
 * 图层 id → 粗语义（与后端 semantic_assign / scheme_generate 五类一致）
 */
export const LAYER_ID_TO_SEMANTIC: Record<string, string> = {
  water: 'water',
  waterway: 'water',
  'waterway-label': 'water',
  'water-line-label': 'water',
  'water-point-label': 'water',
  'road-pedestrian': 'roadnet',
  'road-path': 'roadnet',
  'road-minor': 'roadnet',
  'road-street': 'roadnet',
  'road-secondary-tertiary': 'roadnet',
  'road-primary': 'roadnet',
  'road-motorway-trunk': 'roadnet',
  'road-label': 'roadnet',
  building: 'architecture',
  landcover: 'green',
  'national-park': 'green',
  landuse: 'green',
  'place-label': 'landmark',
  'poi-label': 'landmark',
}

export function semanticForLayerId(layerId: string): string | undefined {
  return LAYER_ID_TO_SEMANTIC[layerId]
}
