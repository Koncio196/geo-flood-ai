<template>
  <div class="sidebar-left" :class="{ 'is-collapsed': !store.isSidebarOpen }">
    
    <div class="layer-content-wrapper">
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
    
  </div>
</template>

<script setup>
import { useMapStore } from '@/stores/mapStore'
const store = useMapStore()
</script>

<style scoped>
/* 1. NADPISANIE GŁÓWNEGO CSS */
/* Przenosimy padding do wewnątrz, aby zlikwidować "skakanie" interfejsu przy chowaniu */
.sidebar-left {
  padding: 0 !important; 
  overflow-x: hidden; /* Ukrywa zawartość, gdy panel robi się węższy niż 300px */
}

/* 2. WEWNĘTRZNY KONTENER (Zabezpieczenie przed zgniataniem) */
.layer-content-wrapper {
  width: 300px; /* Zawsze trzyma oryginalną szerokość panelu */
  padding: 15px; /* Przywrócony padding */
  box-sizing: border-box;
  opacity: 1;
  transition: opacity 0.2s ease; /* Płynne wygaszanie */
}

/* 3. EFEKT ZWIJANIA */
.is-collapsed .layer-content-wrapper {
  opacity: 0;
  pointer-events: none; /* Zapobiega przypadkowym kliknięciom w trakcie zamykania */
}
</style>