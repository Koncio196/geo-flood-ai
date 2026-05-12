<template>
  <div class="feature-info-panel">
    <h3>Informacje o obiekcie</h3>
    <div class="info-content" v-html="store.featureInfoHtml"></div>
  </div>
</template>

<script setup>
import { useMapStore } from '@/stores/mapStore'
const store = useMapStore()
</script>