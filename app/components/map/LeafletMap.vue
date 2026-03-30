<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { MapDataItem } from '~/types/map-data'

const props = defineProps<{
  items: MapDataItem[]
}>()

const mapContainer = ref<HTMLElement | null>(null)
let map: L.Map | null = null
let circlesLayer: L.LayerGroup | null = null

const getCircleColor = (value: number) => {
  if (value < 30) return '#22c55e'
  if (value < 70) return '#f59e0b'
  return '#ef4444'
}

const renderItems = () => {
  if (!map || !circlesLayer) return

  circlesLayer.clearLayers()

  if (!props.items.length) return

  const bounds: L.LatLngExpression[] = []

  props.items.forEach((item) => {
    const latlng: L.LatLngExpression = [item.latitude, item.longitude]
    bounds.push(latlng)

    const circle = L.circleMarker(latlng, {
      radius: 22,
      color: getCircleColor(item.index),
      fillColor: getCircleColor(item.index),
      fillOpacity: 0.9,
      weight: 2
    })

    const icon = L.divIcon({
      className: 'custom-index-marker',
      html: `<div class="index-marker-content">${item.index}</div>`,
      iconSize: [44, 44],
      iconAnchor: [22, 22]
    })

    const labelMarker = L.marker(latlng, { icon, interactive: false })

    const detailsHtml = item.details
      ? Object.entries(item.details)
          .map(([key, value]) => `<div><strong>${key} :</strong> ${String(value)}</div>`)
          .join('')
      : '<div>Aucun détail supplémentaire</div>'

    circle.bindPopup(`
      <div style="min-width:220px">
        <div><strong>${item.name}</strong></div>
        <div><strong>Indice :</strong> ${item.index}</div>
        <div><strong>Zone :</strong> ${item.zone}</div>
        <div><strong>Date :</strong> ${item.date}</div>
        ${detailsHtml}
      </div>
    `)

    circlesLayer?.addLayer(circle)
    circlesLayer?.addLayer(labelMarker)
  })

  if (bounds.length) {
    map.fitBounds(bounds, { padding: [30, 30] })
  }
}

onMounted(async () => {
  await nextTick()

  if (!mapContainer.value) return

  map = L.map(mapContainer.value, {
    zoomControl: true
  }).setView([46.603354, 1.888334], 6)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19
  }).addTo(map)

  circlesLayer = L.layerGroup().addTo(map)

  renderItems()

  setTimeout(() => {
    map?.invalidateSize()
  }, 100)
})

watch(
  () => props.items,
  () => {
    renderItems()
  },
  { deep: true }
)

onBeforeUnmount(() => {
  map?.remove()
  map = null
  circlesLayer = null
})
</script>

<template>
  <ClientOnly>
    <div class="map-wrapper">
      <div ref="mapContainer" class="map-container" />
    </div>
  </ClientOnly>
</template>

<style scoped>
.map-wrapper {
  width: 100%;
  height: 500px;
  min-height: 500px;
}

.map-container {
  width: 100%;
  height: 100%;
  min-height: 500px;
  border-radius: 18px;
  overflow: hidden;
}
</style>

<style>
.leaflet-container {
  width: 100%;
  height: 100%;
}

.custom-index-marker {
  background: transparent;
  border: none;
}

.index-marker-content {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 800;
  color: white;
  pointer-events: none;
}
</style>