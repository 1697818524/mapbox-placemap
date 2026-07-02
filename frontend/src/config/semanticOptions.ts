export const MAP_SEMANTIC_VALUES = [
  'water',
  'roadnet',
  'architecture',
  'green',
  'landmark',
] as const

export type MapSemanticValue = (typeof MAP_SEMANTIC_VALUES)[number]

export interface SemanticOption {
  value: MapSemanticValue
  labelKey: string
}

export const MAP_SEMANTIC_OPTIONS: SemanticOption[] = MAP_SEMANTIC_VALUES.map(value => ({
  value,
  labelKey: `mapStyle.semantics.${value}`,
}))

export const isMapSemanticValue = (value: unknown): value is MapSemanticValue =>
  typeof value === 'string' && MAP_SEMANTIC_VALUES.includes(value as MapSemanticValue)
