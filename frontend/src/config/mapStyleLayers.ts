/** MapStyle 与各页面共用的可配置图层列表（与 Mapbox 样式图层 id 一致） */

export type LayerPaintProperty =
  | 'background-color'
  | 'line-color'
  | 'fill-color'
  | 'fill-extrusion-color'
  | 'fill-outline-color'
  | 'text-color'
  | 'icon-color'

export interface LayerTarget {
  id: string
  paintProperty: LayerPaintProperty
}

export interface LayerConfig {
  id: string
  nameKey: string
  paintProperty: LayerPaintProperty
  defaultColor?: string
  targets?: LayerTarget[]
}

export const baseLayers: LayerConfig[] = [
  {
    id: 'background',
    nameKey: 'background',
    paintProperty: 'background-color',
    defaultColor: '#F3EFEC',
    targets: [
      { id: 'background', paintProperty: 'background-color' },
      { id: 'land', paintProperty: 'background-color' },
      { id: 'land', paintProperty: 'fill-color' },
    ],
  },
]

export const waterLayers: LayerConfig[] = [
  {
    id: 'water',
    nameKey: 'water',
    paintProperty: 'fill-color',
    targets: [
      { id: 'water', paintProperty: 'fill-color' },
      { id: 'waterway', paintProperty: 'line-color' },
    ],
  },
]

export const waterLabelLayers: LayerConfig[] = [
  { id: 'waterway-label', nameKey: 'waterwayLabel', paintProperty: 'text-color' },
  { id: 'water-line-label', nameKey: 'waterLineLabel', paintProperty: 'text-color' },
  { id: 'water-point-label', nameKey: 'waterPointLabel', paintProperty: 'text-color' },
]

export const roadLevel1Layers: LayerConfig[] = [
  {
    id: 'road-level-1',
    nameKey: 'roadLevel1',
    paintProperty: 'line-color',
    targets: [
      { id: 'road-motorway-trunk', paintProperty: 'line-color' },
      { id: 'road-primary', paintProperty: 'line-color' },
    ],
  },
]

export const roadLevel2Layers: LayerConfig[] = [
  {
    id: 'road-level-2',
    nameKey: 'roadLevel2',
    paintProperty: 'line-color',
    targets: [
      { id: 'road-secondary-tertiary', paintProperty: 'line-color' },
      { id: 'road-street', paintProperty: 'line-color' },
    ],
  },
]

export const roadLevel3Layers: LayerConfig[] = [
  {
    id: 'road-level-3',
    nameKey: 'roadLevel3',
    paintProperty: 'line-color',
    targets: [
      { id: 'road-minor', paintProperty: 'line-color' },
      { id: 'road-path', paintProperty: 'line-color' },
      { id: 'road-pedestrian', paintProperty: 'line-color' },
    ],
  },
]

export const roadLabelLayers: LayerConfig[] = [
  { id: 'road-label', nameKey: 'roadLabel', paintProperty: 'text-color' },
]

export const landmarkLabelLayers: LayerConfig[] = [
  { id: 'place-label', nameKey: 'placeLabel', paintProperty: 'text-color' },
  { id: 'poi-label', nameKey: 'poiLabel', paintProperty: 'text-color' },
]

export const roadLayers: LayerConfig[] = [
  ...roadLevel1Layers,
  ...roadLevel2Layers,
  ...roadLevel3Layers,
]

export const buildingLayers: LayerConfig[] = [{ id: 'building', nameKey: 'building', paintProperty: 'fill-color' }]

export const greenLayers: LayerConfig[] = [
  { id: 'landuse', nameKey: 'landuse', paintProperty: 'fill-color' },
]

export const labelLayers: LayerConfig[] = [
  ...waterLabelLayers,
  ...roadLabelLayers,
  ...landmarkLabelLayers,
]

export function getLayerTargets(layer: LayerConfig): LayerTarget[] {
  return layer.targets ?? [{ id: layer.id, paintProperty: layer.paintProperty }]
}

export function getAllConfigurableLayers(options: { includeLabels?: boolean } = {}): LayerConfig[] {
  return [
    ...baseLayers,
    ...waterLayers,
    ...roadLayers,
    ...buildingLayers,
    ...greenLayers,
    ...(options.includeLabels ? labelLayers : []),
  ]
}
