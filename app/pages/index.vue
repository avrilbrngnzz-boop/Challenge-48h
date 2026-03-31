<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import LeafletMap from '~/components/map/LeafletMap.vue'
import type { MapDataItem, MapFilters } from '~/types/map-data'

const items = ref<MapDataItem[]>([])

const filters = reactive<MapFilters>({
  search: '',
  zone: '',
  startDate: '',
  endDate: '',
  minIndex: '',
  maxIndex: ''
})

const filteredItems = computed(() => {
  return items.value.filter((item) => {
    const matchesSearch =
      !filters.search ||
      item.name.toLowerCase().includes(filters.search.toLowerCase()) ||
      item.zone.toLowerCase().includes(filters.search.toLowerCase())

    const matchesZone =
      !filters.zone || item.zone.toLowerCase().includes(filters.zone.toLowerCase())

    const itemDate = new Date(item.date).getTime()
    const start = filters.startDate ? new Date(filters.startDate).getTime() : null
    const end = filters.endDate ? new Date(filters.endDate).getTime() : null

    const matchesStart = start === null || itemDate >= start
    const matchesEnd = end === null || itemDate <= end

    const min = filters.minIndex !== '' ? Number(filters.minIndex) : null
    const max = filters.maxIndex !== '' ? Number(filters.maxIndex) : null

    const matchesMin = min === null || item.index >= min
    const matchesMax = max === null || item.index <= max

    return (
      matchesSearch &&
      matchesZone &&
      matchesStart &&
      matchesEnd &&
      matchesMin &&
      matchesMax
    )
  })
})

const pointsCount = computed(() => filteredItems.value.length)

const zonesCount = computed(() => {
  return new Set(filteredItems.value.map((item) => item.zone)).size
})

const alertsCount = computed(() => {
  return filteredItems.value.filter((item) => item.index >= 70).length
})

const averageIndex = computed(() => {
  if (!filteredItems.value.length) return 0

  const total = filteredItems.value.reduce((sum, item) => sum + item.index, 0)
  return Math.round(total / filteredItems.value.length)
})

const indexDistribution = computed(() => {
  return {
    low: filteredItems.value.filter((item) => item.index < 30).length,
    medium: filteredItems.value.filter((item) => item.index >= 30 && item.index < 70).length,
    high: filteredItems.value.filter((item) => item.index >= 70).length
  }
})

const timelineData = computed(() => {
  const grouped: Record<string, number[]> = {}

  filteredItems.value.forEach((item) => {
    const day = item.date.slice(0, 10)

    if (!grouped[day]) grouped[day] = []
    grouped[day].push(item.index)
  })

  return Object.entries(grouped)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, values]) => ({
      date,
      average: Math.round(values.reduce((sum, value) => sum + value, 0) / values.length)
    }))
})

const resetFilters = () => {
  filters.search = ''
  filters.zone = ''
  filters.startDate = ''
  filters.endDate = ''
  filters.minIndex = ''
  filters.maxIndex = ''
}
</script>

<template>
  <main class="dashboard">
    <header class="topbar">
      <div>
        <h1>Dashboard de supervision</h1>
        <p class="subtitle">
          Vue d’ensemble de la plateforme, des données cartographiques et des indicateurs clés.
        </p>
      </div>
    </header>

    <section class="stats-grid">
      <article class="stat-card">
        <p class="stat-label">Points analysés</p>
        <div class="stat-row">
          <h2>{{ pointsCount }}</h2>
          <span class="trend neutral">--</span>
        </div>
      </article>

      <article class="stat-card">
        <p class="stat-label">Zones surveillées</p>
        <div class="stat-row">
          <h2>{{ zonesCount }}</h2>
          <span class="trend neutral">--</span>
        </div>
      </article>

      <article class="stat-card">
        <p class="stat-label">Alertes actives</p>
        <div class="stat-row">
          <h2>{{ alertsCount }}</h2>
          <span class="trend neutral">--</span>
        </div>
      </article>

      <article class="stat-card">
        <p class="stat-label">Indice moyen</p>
        <div class="stat-row">
          <h2>{{ averageIndex }}</h2>
          <span class="trend neutral">--</span>
        </div>
      </article>
    </section>

    <section class="toolbar card">
      <div class="toolbar-grid">
        <div class="field">
          <label>Recherche</label>
          <input
            v-model="filters.search"
            type="text"
            placeholder="Zone, point, indicateur..."
          />
        </div>

        <div class="field">
          <label>Zone</label>
          <input
            v-model="filters.zone"
            type="text"
            placeholder="Ex: paris"
          />
        </div>

        <div class="field">
          <label>Date début</label>
          <input v-model="filters.startDate" type="date" />
        </div>

        <div class="field">
          <label>Date fin</label>
          <input v-model="filters.endDate" type="date" />
        </div>

        <div class="field">
          <label>Indice min</label>
          <input v-model="filters.minIndex" type="number" min="0" />
        </div>

        <div class="field">
          <label>Indice max</label>
          <input v-model="filters.maxIndex" type="number" min="0" />
        </div>
      </div>

      <div class="toolbar-actions">
        <button class="btn btn-secondary" @click="resetFilters">
          Réinitialiser
        </button>
      </div>
    </section>

    <section class="main-grid">
      <div class="main-column">
        <section class="card hero-panel">
          <div class="panel-head">
            <div>
              <p class="panel-kicker">Vue principale</p>
              <h3>Carte / visualisation principale</h3>
            </div>
            <span class="badge">{{ filteredItems.length }} résultat(s)</span>
          </div>

          <LeafletMap :items="filteredItems" />

          <p v-if="filteredItems.length === 0" class="empty-map-message">
            Aucune donnée disponible pour le moment.
          </p>
        </section>

        <section class="grid-2">
          <article class="card widget">
            <div class="panel-head">
              <h3>Répartition des indices</h3>
              <span class="badge muted">Graphique</span>
            </div>

            <div class="mini-chart">
              <div class="bar-row">
                <span class="bar-label">Faible</span>
                <div class="bar-track">
                  <div
                    class="bar-fill green"
                    :style="{ width: `${Math.max(indexDistribution.low * 40, indexDistribution.low ? 16 : 0)}px` }"
                  />
                </div>
                <strong>{{ indexDistribution.low }}</strong>
              </div>

              <div class="bar-row">
                <span class="bar-label">Moyen</span>
                <div class="bar-track">
                  <div
                    class="bar-fill orange"
                    :style="{ width: `${Math.max(indexDistribution.medium * 40, indexDistribution.medium ? 16 : 0)}px` }"
                  />
                </div>
                <strong>{{ indexDistribution.medium }}</strong>
              </div>

              <div class="bar-row">
                <span class="bar-label">Élevé</span>
                <div class="bar-track">
                  <div
                    class="bar-fill red"
                    :style="{ width: `${Math.max(indexDistribution.high * 40, indexDistribution.high ? 16 : 0)}px` }"
                  />
                </div>
                <strong>{{ indexDistribution.high }}</strong>
              </div>
            </div>
          </article>

          <article class="card widget">
            <div class="panel-head">
              <h3>Évolution temporelle</h3>
              <span class="badge muted">Timeline</span>
            </div>

            <div v-if="timelineData.length" class="timeline-list">
              <div
                v-for="entry in timelineData"
                :key="entry.date"
                class="timeline-row"
              >
                <span>{{ entry.date }}</span>
                <strong>{{ entry.average }}</strong>
              </div>
            </div>

            <div v-else class="widget-placeholder small">
              <p>Aucune donnée disponible.</p>
            </div>
          </article>
        </section>
      </div>

      <aside class="side-column">
        <section class="card side-widget">
          <div class="system-row">
            <span>Dernière mise à jour</span>
            <strong>--:--</strong>
          </div>
        </section>

        <section class="card side-widget">
          <div class="panel-head">
            <h3>Légende</h3>
          </div>

          <div class="legend-list">
            <div class="legend-item">
              <span class="legend-dot green"></span>
              <span>Indice faible (&lt; 30)</span>
            </div>
            <div class="legend-item">
              <span class="legend-dot orange"></span>
              <span>Indice moyen (30 - 69)</span>
            </div>
            <div class="legend-item">
              <span class="legend-dot red"></span>
              <span>Indice élevé (70+)</span>
            </div>
          </div>
        </section>
      </aside>
    </section>
  </main>
</template>

<style scoped>
.dashboard {
  min-height: 100vh;
  padding: 32px;
  background:
    radial-gradient(circle at top left, rgba(59, 130, 246, 0.12), transparent 22%),
    radial-gradient(circle at bottom right, rgba(16, 185, 129, 0.08), transparent 18%),
    linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 24px;
}

h1 {
  margin: 0;
  font-size: 34px;
  line-height: 1.1;
  color: #0f172a;
}

.subtitle {
  margin-top: 12px;
  max-width: 760px;
  color: #475569;
  font-size: 15px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  padding: 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(10px);
}

.stat-label {
  margin: 0 0 10px;
  font-size: 14px;
  color: #64748b;
  font-weight: 600;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.stat-row h2 {
  margin: 0;
  font-size: 30px;
  color: #0f172a;
}

.trend {
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
}

.trend.neutral {
  background: #e2e8f0;
  color: #475569;
}

.card {
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(10px);
  border-radius: 20px;
}

.toolbar {
  padding: 18px;
  margin-bottom: 20px;
}

.toolbar-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.toolbar-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field label {
  font-size: 13px;
  font-weight: 700;
  color: #334155;
}

.field input {
  height: 44px;
  border-radius: 12px;
  border: 1px solid #cbd5e1;
  background: white;
  padding: 0 14px;
  font-size: 14px;
}

.main-grid {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(300px, 380px);
  gap: 20px;
  align-items: start;
}

.main-column {
  display: grid;
  gap: 20px;
}

.side-column {
  display: grid;
  gap: 20px;
}

.hero-panel,
.widget,
.side-widget {
  padding: 20px;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.panel-kicker {
  margin: 0 0 6px;
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #3b82f6;
}

.panel-head h3 {
  margin: 0;
  font-size: 18px;
  color: #0f172a;
}

.badge {
  padding: 6px 10px;
  border-radius: 999px;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
}

.badge.muted {
  background: #e2e8f0;
  color: #475569;
}

.empty-map-message {
  margin: 16px 0 0;
  color: #64748b;
  font-size: 14px;
  text-align: center;
}

.grid-2 {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.widget-placeholder.small {
  min-height: 220px;
  border-radius: 16px;
  border: 2px dashed #cbd5e1;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 20px;
  color: #64748b;
  background: #f8fafc;
}

.system-list,
.legend-list {
  display: grid;
  gap: 12px;
}

.system-row,
.legend-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #334155;
}

.legend-item {
  justify-content: flex-start;
  align-items: center;
}

.legend-dot {
  width: 14px;
  height: 14px;
  border-radius: 999px;
  display: inline-block;
}

.legend-dot.green {
  background: #22c55e;
}

.legend-dot.orange {
  background: #f59e0b;
}

.legend-dot.red {
  background: #ef4444;
}

.btn {
  height: 42px;
  padding: 0 16px;
  border-radius: 12px;
  border: none;
  cursor: pointer;
  font-weight: 700;
}

.btn-secondary {
  background: #e2e8f0;
  color: #1e293b;
}

.mini-chart {
  display: grid;
  gap: 16px;
}

.bar-row {
  display: grid;
  grid-template-columns: 70px 1fr 30px;
  align-items: center;
  gap: 12px;
}

.bar-label {
  font-size: 14px;
  color: #334155;
  font-weight: 600;
}

.bar-track {
  height: 14px;
  background: #e2e8f0;
  border-radius: 999px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 999px;
}

.bar-fill.green {
  background: #22c55e;
}

.bar-fill.orange {
  background: #f59e0b;
}

.bar-fill.red {
  background: #ef4444;
}

.timeline-list {
  display: grid;
  gap: 12px;
}

.timeline-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  color: #334155;
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .toolbar-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .main-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .dashboard {
    padding: 18px;
  }

  .stats-grid,
  .toolbar-grid,
  .grid-2 {
    grid-template-columns: 1fr;
  }

  h1 {
    font-size: 28px;
  }
}
</style>