<script setup lang="ts">
import type { MapDataItem } from '~/types/map-data'

defineProps<{
  items: MapDataItem[]
}>()

const getStatusClass = (index: number) => {
  if (index < 30) return 'low'
  if (index < 70) return 'medium'
  return 'high'
}
</script>

<template>
  <div class="list">
    <article
      v-for="item in items"
      :key="item.id"
      class="list-item"
    >
      <div class="top-row">
        <div>
          <h3>{{ item.name }}</h3>
          <p>{{ item.details?.city ?? item.zone }}</p>
        </div>

        <span class="index-badge" :class="getStatusClass(item.index)">
          {{ item.index }}
        </span>
      </div>

      <div class="meta">
        <span>Zone : {{ item.zone }}</span>
        <span>{{ new Date(item.date).toLocaleDateString() }}</span>
      </div>
    </article>
  </div>
</template>

<style scoped>
.list {
  display: grid;
  gap: 12px;
  max-height: 540px;
  overflow: auto;
  padding-right: 4px;
}

.list-item {
  padding: 14px;
  border-radius: 14px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.top-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

h3 {
  margin: 0 0 4px;
  font-size: 15px;
  color: #0f172a;
}

p {
  margin: 0;
  font-size: 13px;
  color: #64748b;
}

.meta {
  margin-top: 10px;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  font-size: 12px;
  color: #475569;
}

.index-badge {
  min-width: 52px;
  text-align: center;
  padding: 8px 10px;
  border-radius: 999px;
  font-weight: 800;
  color: white;
}

.low {
  background: #16a34a;
}

.medium {
  background: #f59e0b;
}

.high {
  background: #ef4444;
}
</style>