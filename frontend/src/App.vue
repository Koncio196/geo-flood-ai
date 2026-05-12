<template>
  <div class="container" :class="{ 'sidebar-closed': !store.isSidebarOpen }">
    
    <div class="header">
      GeoFloodAI
    </div>

    <LayerPanel />
    <MapViewer />

    <div class="sidebar-right">
      <FeaturePanel />
      <ChatPanel />
    </div>

    <div class="footer">
      <div class="footer-left">
        Układ wyświetlania: EPSG:3857 (WGS 84 / Pseudo-Mercator)
      </div>
      <div class="footer-center" id="mouse-coords">
        Lat: {{ store.coordinates.lat }}, Lon: {{ store.coordinates.lon }}
      </div>
      <div class="footer-right">
        Autor: Paweł Konecki
      </div>
    </div>
    
  </div>
</template>

<script setup>
import { useMapStore } from '@/stores/mapStore'
import LayerPanel from '@/components/LayerPanel.vue'
import MapViewer from '@/components/MapViewer.vue'
import FeaturePanel from '@/components/FeaturePanel.vue'
import ChatPanel from '@/components/ChatPanel.vue'

const store = useMapStore()
</script>