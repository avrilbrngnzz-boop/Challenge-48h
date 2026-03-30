<script setup lang="ts">
import type { DataFilters as Filters } from '~/types/map-data'

const emit = defineEmits<{
  apply: [filters: Filters]
}>()

const filters = reactive<Filters>({
  dateStart: '',
  dateEnd: '',
  minIndex: undefined,
  maxIndex: undefined,
  zone: ''
})

const submitFilters = () => {
  emit('apply', {
    dateStart: filters.dateStart || undefined,
    dateEnd: filters.dateEnd || undefined,
    minIndex: filters.minIndex,
    maxIndex: filters.maxIndex,
    zone: filters.zone || undefined
  })
}

const resetFilters = () => {
  filters.dateStart = ''
  filters.dateEnd = ''
  filters.minIndex = undefined
  filters.maxIndex = undefined
  filters.zone = ''
  submitFilters()
}
</script>

<template>
  <form class="filters-card" @submit.prevent="submitFilters">
    <div class="field">
      <label for="dateStart">Date début</label>
      <input id="dateStart" v-model="filters.dateStart" type="date" />
    </div>

    <div class="field">
      <label for="dateEnd">Date fin</label>
      <input id="dateEnd" v-model="filters.dateEnd" type="date" />
    </div>

    <div class="field">
      <label for="minIndex">Indice min</label>
      <input id="minIndex" v-model.number="filters.minIndex" type="number" min="0" />
    </div>

    <div class="field">
      <label for="maxIndex">Indice max</label>
      <input id="maxIndex" v-model.number="filters.maxIndex" type="number" min="0" />
    </div>

    <div class="field">
      <label for="zone">Zone</label>
      <select id="zone" v-model="filters.zone">
        <option value="">Toutes</option>
        <option value="paris">Paris</option>
        <option value="lyon">Lyon</option>
        <option value="marseille">Marseille</option>
      </select>
    </div>

    <div class="actions">
      <button type="submit" class="primary">Appliquer</button>
      <button type="button" class="secondary" @click="resetFilters">
        Réinitialiser
      </button>
    </div>
  </form>
</template>

<style scoped>
.filters-card {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 14px;
  padding: 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(148, 163, 184, 0.2);
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

label {
  font-size: 13px;
  font-weight: 700;
  color: #334155;
}

input,
select {
  height: 42px;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  padding: 0 12px;
  font-size: 14px;
  background: white;
}

input:focus,
select:focus {
  outline: none;
  border-color: #3b82f6;
}

.actions {
  display: flex;
  gap: 10px;
  align-items: end;
}

button {
  height: 42px;
  border: none;
  border-radius: 12px;
  padding: 0 16px;
  font-weight: 700;
  cursor: pointer;
}

.primary {
  background: #2563eb;
  color: white;
}

.secondary {
  background: #e2e8f0;
  color: #1e293b;
}

@media (max-width: 1100px) {
  .filters-card {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .filters-card {
    grid-template-columns: 1fr;
  }

  .actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>