export interface MapDataItem {
  id: string | number
  name: string
  latitude: number
  longitude: number
  index: number
  date: string
  zone: string
  details?: Record<string, unknown>
}

export interface MapFilters {
  search: string
  zone: string
  startDate: string
  endDate: string
  minIndex: string
  maxIndex: string
}