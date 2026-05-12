<template>
  <div class="sidebar-left">
    <h3>Podkłady mapowe</h3>
    <div id="map-list">
      <div v-for="map in store.baseMaps" :key="map.id" class="layer-item">
        <span class="layer-label">{{ map.name }}</span>
        <label class="switch">
          <input type="checkbox" :checked="map.visible" @change="store.toggleLayerVisibility(map.id, true)">
          <span class="slider"></span>
        </label>
      </div>
    </div>

    <h3>Warstwy</h3>
    <div id="layer-list">
      <div v-for="layer in store.overlays" :key="layer.id" 
           class="layer-item" 
           :class="{ selected: store.activeLayerId === layer.id }"
           @click.self="store.setActiveQueryLayer(layer.id)">
        
        <label class="switch">
          <input type="checkbox" :checked="layer.visible" @change="store.toggleLayerVisibility(layer.id, false)">
          <span class="slider"></span>
        </label>
        <span class="layer-label" @click="store.setActiveQueryLayer(layer.id)">{{ layer.name }}</span>
      </div>
    </div>

    <div id="legend-container">
      <h3>Legenda</h3>
      </div>
  </div>
</template>

<script setup>
import { useMapStore } from '@/stores/mapStore'
const store = useMapStore()
</script>