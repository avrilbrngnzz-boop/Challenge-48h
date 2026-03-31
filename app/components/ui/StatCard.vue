<script setup lang="ts">
defineProps<{
  title: string
  value: string | number
}>()
</script>

<template>
  <article class="stat-card">
    <p class="label">{{ title }}</p>
    <p class="value">{{ value }}</p>
  </article>
</template>

<style scoped>
.stat-card {
  padding: 20px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(148, 163, 184, 0.2);
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(10px);
}

.label {
  margin: 0 0 10px;
  color: #64748b;
  font-size: 14px;
  font-weight: 600;
}

.value {
  margin: 0;
  color: #0f172a;
  font-size: 30px;
  font-weight: 800;
}
</style>