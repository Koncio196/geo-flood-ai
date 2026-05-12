<template>
  <div id="map" ref="mapContainer">
    <div class="map-tools">
      <button class="tool-btn" @click="zoom(1)" title="Przybliż">+</button>
      <button class="tool-btn" @click="zoom(-1)" title="Oddal">-</button>
      <button id="btn-sidebar-toggle" class="tool-btn active" title="Pokaż/Ukryj panel" @click="store.toggleSidebar" style="margin-top: 5px">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
            <polyline points="2 17 12 22 22 17"></polyline>
            <polyline points="2 12 12 17 22 12"></polyline>
        </svg>
      </button>
      <button class="tool-btn" id="btn-measure-dist" title="Pomiar odległości" style="margin-top: 10px">📏</button>
      <button class="tool-btn" id="btn-measure-area" title="Pomiar powierzchni">⬠</button>
    </div>

    <div v-if="isTimelapseVisible" class="time-slider-container">
      <div class="time-slider-header">
        Data obrazowania: <strong>{{ store.currentTimelapseDate }}</strong>
      </div>
      <input type="range" id="time-slider" :min="0" :max="store.timelapseDates.length - 1" v-model="store.currentTimelapseIndex" @click.stop>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useMapStore } from '@/stores/mapStore'
import Map from 'ol/Map'
import View from 'ol/View'
import TileLayer from 'ol/layer/Tile'
import OSM from 'ol/source/OSM'
import TileWMS from 'ol/source/TileWMS'
import { fromLonLat, toLonLat } from 'ol/proj'

const store = useMapStore()
const mapContainer = ref(null)
let olMap = null
const olLayers = {} // Obiekt przechowujący instancje warstw OpenLayers

const isTimelapseVisible = computed(() => {
  const layer = store.overlays.find(l => l.id === 'timelapse')
  return layer && layer.visible
})

onMounted(() => {
  // 1. Inicjalizacja Mapy
  olMap = new Map({
    target: mapContainer.value,
    view: new View({
      center: fromLonLat([17.02, 50.67]),
      zoom: 8,
    }),
    controls: [] 
  })

  // 2. Budowa warstw podkładowych
  olLayers['osm'] = new TileLayer({ source: new OSM(), visible: false, zIndex: 1 })
  olMap.addLayer(olLayers['osm'])
  
  olLayers['ortofoto'] = new TileLayer({
    source: new TileWMS({
      url: '/geoserver/wms',
      params: { 'LAYERS': 'flood_ai:ORTOFOTOMAPA', 'TILED': true },
      serverType: 'geoserver',
    }),
    visible: false, zIndex: 0
  })
  olMap.addLayer(olLayers['ortofoto'])

  // 3. Budowa warstw nakładkowych (WMS)
  store.overlays.forEach(layer => {
    const sourceParams = { 'LAYERS': layer.layerName, 'TILED': true }
    if (layer.isTimelapse) {
      sourceParams['TIME'] = store.currentTimelapseDate
    }

    olLayers[layer.id] = new TileLayer({
      source: new TileWMS({
        url: '/geoserver/wms',
        params: sourceParams,
        serverType: 'geoserver',
      }),
      visible: layer.visible,
      zIndex: 10 // Uproszczony Z-Index dla przykładu
    })
    olMap.addLayer(olLayers[layer.id])
  })

  // 4. Śledzenie kursora
  olMap.on('pointermove', (evt) => {
    if (evt.dragging) return
    const coords = toLonLat(evt.coordinate)
    store.updateCoordinates(coords[1].toFixed(4), coords[0].toFixed(4)) // Lat, Lon
  })

  // 5. ZAPYTANIE GetFeatureInfo (Kliknięcie)
  olMap.on('singleclick', async (evt) => {
    if (!store.activeLayerId) {
      store.featureInfoHtml = '<p style="color: #cc0000; font-weight: bold;">Najpierw zaznacz warstwę na liście po lewej stronie.</p>'
      return
    }

    store.featureInfoHtml = '<p>Pobieranie atrybutów z bazy PostGIS...</p>'
    const activeLayer = olLayers[store.activeLayerId]
    const viewResolution = olMap.getView().getResolution()
    
    // Potężna funkcja OpenLayers - sama buduje URL do WMS-a!
    const url = activeLayer.getSource().getFeatureInfoUrl(
      evt.coordinate, viewResolution, 'EPSG:3857', { 'INFO_FORMAT': 'application/json' }
    )

    if (url) {
      try {
        const response = await fetch(url)
        const data = await response.json()
        if (data.features && data.features.length > 0) {
          const props = data.features[0].properties
          let tableHtml = '<table><tr><th>Atrybut</th><th>Wartość</th></tr>'
          for (const key in props) {
            tableHtml += `<tr><td><strong>${key}</strong></td><td>${props[key]}</td></tr>`
          }
          tableHtml += '</table>'
          store.featureInfoHtml = tableHtml
        } else {
          store.featureInfoHtml = '<p>Brak obiektów w klikniętym miejscu.</p>'
        }
      } catch (err) {
        store.featureInfoHtml = '<p style="color: red;">Błąd komunikacji z GeoServerem.</p>'
      }
    }
  })
})

// Obserwatory (Watchers) - Reaktywność Vue połączona z OpenLayers
watch(() => store.baseMaps, (newBaseMaps) => {
  newBaseMaps.forEach(map => olLayers[map.id].setVisible(map.visible))
}, { deep: true })

watch(() => store.overlays, (newOverlays) => {
  newOverlays.forEach(layer => olLayers[layer.id].setVisible(layer.visible))
}, { deep: true })

// Aktualizacja warstwy Timelapse
watch(() => store.currentTimelapseDate, (newDate) => {
  if(olLayers['timelapse']) {
    // Aktualizujemy parametr TIME źródła i odświeżamy kafelki!
    olLayers['timelapse'].getSource().updateParams({ 'TIME': newDate })
  }
})

const zoom = (delta) => {
  if (!olMap) return
  const view = olMap.getView()
  view.animate({ zoom: view.getZoom() + delta, duration: 250 })
}
</script>