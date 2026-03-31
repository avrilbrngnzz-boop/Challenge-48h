<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet.markercluster'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'
import type { MapDataItem } from '~/types/map-data'

const props = defineProps<{
  items: MapDataItem[]
}>()

const mapContainer = ref<HTMLElement | null>(null)

let map: L.Map | null = null
let markerClusterGroup: L.MarkerClusterGroup | null = null

const getCircleColor = (value: number) => {
  if (value < 30) return '#22c55e'
  if (value < 70) return '#f59e0b'
  return '#ef4444'
}

const createPointMarker = (item: MapDataItem) => {
  const color = getCircleColor(item.index)

  const icon = L.divIcon({
    className: 'custom-point-icon',
    html: `
      <div
        class="point-badge"
        style="
          background:${color};
          border:2px solid ${color};
        "
      >
        ${item.index}
      </div>
    `,
    iconSize: [44, 44],
    iconAnchor: [22, 22]
  })

  const marker = L.marker([item.latitude, item.longitude], { icon })

  const detailsHtml = item.details
    ? Object.entries(item.details)
        .map(([key, value]) => `<div><strong>${key} :</strong> ${String(value)}</div>`)
        .join('')
    : '<div>Aucun détail supplémentaire</div>'

  marker.bindPopup(`
    <div style="min-width:220px">
      <div><strong>${item.name}</strong></div>
      <div><strong>Indice :</strong> ${item.index}</div>
      <div><strong>Zone :</strong> ${item.zone}</div>
      <div><strong>Date :</strong> ${item.date}</div>
      ${detailsHtml}
    </div>
  `)

  return marker
}

const renderItems = () => {
  if (!map || !markerClusterGroup) return

  markerClusterGroup.clearLayers()

  if (!props.items.length) return

  const markers = props.items.map(createPointMarker)
  markerClusterGroup.addLayers(markers)

  const bounds = markerClusterGroup.getBounds()
  if (bounds.isValid()) {
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

  markerClusterGroup = L.markerClusterGroup({
    showCoverageOnHover: false,
    spiderfyOnMaxZoom: true,
    zoomToBoundsOnClick: true,
    removeOutsideVisibleBounds: true,
    maxClusterRadius: 50,
    iconCreateFunction(cluster) {
      const count = cluster.getChildCount()

      return L.divIcon({
        html: `
          <div class="cluster-badge">
            ${count}
          </div>
        `,
        className: 'custom-cluster-icon',
        iconSize: L.point(52, 52)
      })
    }
  })

  map.addLayer(markerClusterGroup)

  renderItems()

  setTimeout(() => {
    map?.invalidateSize()
  }, 150)
})

watch(
  () => props.items,
  () => {
    renderItems()
  },
  { deep: true }
)

onBeforeUnmount(() => {
  if (map && markerClusterGroup) {
    map.removeLayer(markerClusterGroup)
  }

  markerClusterGroup = null
  map?.remove()
  map = null
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

.custom-point-icon {
  background: transparent;
  border: none;
}

.point-badge {
  width: 44px;
  height: 44px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
  font-weight: 800;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.2);
}

.custom-cluster-icon {
  background: transparent;
  border: none;
}

.cluster-badge {
  width: 52px;
  height: 52px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #2563eb;
  color: white;
  font-size: 14px;
  font-weight: 800;
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.35);
  border: 3px solid white;
}
</style>