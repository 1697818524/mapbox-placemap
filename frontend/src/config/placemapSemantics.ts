/**
 * 图层控制项 id -> 粗语义（与后端 semantic_assign / scheme_generate 五类一致）
 */
export const LAYER_ID_TO_SEMANTIC: Record<string, string> = {
  water: 'water',
  'road-level-1': 'roadnet',
  'road-level-2': 'roadnet',
  'road-level-3': 'roadnet',
  building: 'architecture',
  landuse: 'green',
  'waterway-label': 'water',
  'water-line-label': 'water',
  'water-point-label': 'water',
  'road-label': 'roadnet',
  'place-label': 'landmark',
  'poi-label': 'landmark',
}

export function semanticForLayerId(layerId: string): string | undefined {
  return LAYER_ID_TO_SEMANTIC[layerId]
}
