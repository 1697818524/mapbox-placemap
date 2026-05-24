/** MapStyle 与各页面共用的可配置图层列表（与 Mapbox 样式图层 id 一致） */

export type LayerPaintProperty =
  | 'line-color'
  | 'fill-color'
  | 'fill-outline-color'
  | 'text-color'
  | 'icon-color'

export interface LayerConfig {
  id: string
  nameKey: string
  paintProperty: LayerPaintProperty
  defaultColor?: string
}

export const waterLayers: LayerConfig[] = [
  { id: 'water', nameKey: 'water', paintProperty: 'fill-color' },
  { id: 'waterway', nameKey: 'waterway', paintProperty: 'line-color' },
]

export const roadLayers: LayerConfig[] = [
  { id: 'road-pedestrian', nameKey: 'roadPedestrian', paintProperty: 'line-color' },
  { id: 'road-path', nameKey: 'roadPath', paintProperty: 'line-color' },
  { id: 'road-minor', nameKey: 'roadMinor', paintProperty: 'line-color' },
  { id: 'road-street', nameKey: 'roadStreet', paintProperty: 'line-color' },
  { id: 'road-secondary-tertiary', nameKey: 'roadSecondaryTertiary', paintProperty: 'line-color' },
  { id: 'road-primary', nameKey: 'roadPrimary', paintProperty: 'line-color' },
  { id: 'road-motorway-trunk', nameKey: 'roadMotorwayTrunk', paintProperty: 'line-color' },
]

export const buildingLayers: LayerConfig[] = [{ id: 'building', nameKey: 'building', paintProperty: 'fill-color' }]

export const greenLayers: LayerConfig[] = [
  { id: 'landcover', nameKey: 'landcover', paintProperty: 'fill-color' },
  { id: 'national-park', nameKey: 'nationalPark', paintProperty: 'fill-color' },
  { id: 'landuse', nameKey: 'landuse', paintProperty: 'fill-color' },
]

export const labelLayers: LayerConfig[] = [
  { id: 'waterway-label', nameKey: 'waterwayLabel', paintProperty: 'icon-color' },
  { id: 'water-line-label', nameKey: 'waterLineLabel', paintProperty: 'icon-color' },
  { id: 'water-point-label', nameKey: 'waterPointLabel', paintProperty: 'icon-color' },
  { id: 'road-label', nameKey: 'roadLabel', paintProperty: 'icon-color' },
  { id: 'place-label', nameKey: 'placeLabel', paintProperty: 'icon-color' },
  { id: 'poi-label', nameKey: 'poiLabel', paintProperty: 'icon-color' },
]

export function getAllConfigurableLayers(): LayerConfig[] {
  return [...waterLayers, ...roadLayers, ...buildingLayers, ...greenLayers, ...labelLayers]
}
