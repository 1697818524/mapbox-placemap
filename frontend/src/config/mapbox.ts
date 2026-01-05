/**
 * Mapbox 配置
 */
export const MAPBOX_CONFIG = {
  ACCESS_TOKEN:
    import.meta.env.VITE_MAPBOX_TOKEN ||
    'pk.eyJ1IjoiZGYweGV3YyIsImEiOiJjbTNoamh0NnMwZzZ6MnRwcXJkbWUxM2syIn0.eE5V7j0-uNb4WiwG2hXs0w',
  DEFAULT_STYLE: 'mapbox://styles/mapbox/streets-v12',
  GEOCODING_API_URL: 'https://api.mapbox.com/geocoding/v5/mapbox.places',
} as const
