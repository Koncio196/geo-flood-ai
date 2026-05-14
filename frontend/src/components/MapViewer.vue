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
      
      <button class="tool-btn" :class="{ 'active': activeMeasurementTool === 'length' }" @click="toggleMeasurement('length')" title="Pomiar odległości" style="margin-top: 10px">📏</button>
      <button class="tool-btn" :class="{ 'active': activeMeasurementTool === 'area' }" @click="toggleMeasurement('area')" title="Pomiar powierzchni">⬠</button>
      <button class="tool-btn danger" @click="clearMeasurements" title="Kasuj pomiary">🗑️</button>
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

// --- GŁÓWNE IMPORTY OPENLAYERS ---
import Map from 'ol/Map'
import View from 'ol/View'
import TileLayer from 'ol/layer/Tile'
import OSM from 'ol/source/OSM'
import TileWMS from 'ol/source/TileWMS'
import { fromLonLat, toLonLat, transform } from 'ol/proj'

// --- IMPORTY PROJ4 (DLA EPSG:2180) ---
import proj4 from 'proj4'
import { register } from 'ol/proj/proj4'

// --- REJESTRACJA UKŁADU PUWG 1992 (EPSG:2180) ---
proj4.defs("EPSG:2180", "+proj=tmerc +lat_0=0 +lon_0=19 +k=0.9993 +x_0=500000 +y_0=-5300000 +ellps=GRS80 +units=m +no_defs");
register(proj4);

// --- IMPORTY DO POMIARÓW I RYSOWANIA ---
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import Draw from 'ol/interaction/Draw'
import Overlay from 'ol/Overlay'
import { Style, Fill, Stroke, Circle as CircleStyle } from 'ol/style'
import { getArea, getLength } from 'ol/sphere'
import { unByKey } from 'ol/Observable'

// ==========================================
// ZMIENNE DO KONFIGURACJI SKALI MAPY
// ==========================================
const MIN_ZOOM = 9;  // Minimalny zoom (oddalenie)
const MAX_ZOOM = 20; // Maksymalny zoom (przybliżenie)

const store = useMapStore()
const mapContainer = ref(null)
let olMap = null
const olLayers = {} 

// --- STAN I ZMIENNE DLA POMIARÓW ---
const activeMeasurementTool = ref(null)
let measureSource = null
let measureLayer = null
let drawInteraction = null
let measureTooltipElement = null
let measureTooltipOverlay = null
let sketch = null
let listener = null

const isTimelapseVisible = computed(() => {
  const layer = store.overlays.find(l => l.id === 'timelapse')
  return layer && layer.visible
})

// Funkcja tworząca dynamiczny "dymek" na bieżący wynik pomiaru
const createMeasureTooltip = () => {
  if (measureTooltipElement) {
    measureTooltipElement.parentNode.removeChild(measureTooltipElement)
  }
  measureTooltipElement = document.createElement('div')
  measureTooltipElement.className = 'ol-tooltip ol-tooltip-measure'
  measureTooltipOverlay = new Overlay({
    element: measureTooltipElement,
    offset: [0, -15],
    positioning: 'bottom-center',
    stopEvent: false,
    insertFirst: false,
  })
  olMap.addOverlay(measureTooltipOverlay)
}

// Funkcja aktywująca/dezaktywująca narzędzie rysowania
const toggleMeasurement = (type) => {
  if (drawInteraction) {
    olMap.removeInteraction(drawInteraction)
    drawInteraction = null
  }

  if (activeMeasurementTool.value === type) {
    activeMeasurementTool.value = null
    return 
  }

  activeMeasurementTool.value = type
  
  const geometryType = type === 'length' ? 'LineString' : 'Polygon'
  
  drawInteraction = new Draw({
    source: measureSource,
    type: geometryType,
    style: new Style({
      fill: new Fill({ color: 'rgba(255, 255, 255, 0.2)' }),
      stroke: new Stroke({ color: 'rgba(0, 0, 0, 0.5)', lineDash: [10, 10], width: 2 }),
      image: new CircleStyle({ radius: 5, stroke: new Stroke({ color: 'rgba(0, 0, 0, 0.7)' }), fill: new Fill({ color: 'rgba(255, 255, 255, 0.2)' }) })
    })
  })

  olMap.addInteraction(drawInteraction)
  createMeasureTooltip()

  drawInteraction.on('drawstart', (evt) => {
    sketch = evt.feature
    let tooltipCoord = evt.coordinate

    listener = sketch.getGeometry().on('change', (evt) => {
      const geom = evt.target
      let output
      if (geom.getType() === 'Polygon') {
        const area = getArea(geom)
        output = (area / 10000).toFixed(3) + ' ha'
        tooltipCoord = geom.getInteriorPoint().getCoordinates()
      } else if (geom.getType() === 'LineString') {
        const length = getLength(geom)
        output = (length / 1000).toFixed(3) + ' km'
        tooltipCoord = geom.getLastCoordinate()
      }
      measureTooltipElement.innerHTML = output
      measureTooltipOverlay.setPosition(tooltipCoord)
    })
  })

  drawInteraction.on('drawend', () => {
    measureTooltipElement.className = 'ol-tooltip ol-tooltip-static'
    measureTooltipOverlay.setOffset([0, -7])
    sketch = null
    measureTooltipElement = null
    createMeasureTooltip() 
    unByKey(listener)
  })
}

// Funkcja czyszczenia mapy z pomiarów i rysunków
const clearMeasurements = () => {
  if (measureSource) measureSource.clear()
  
  const overlays = olMap.getOverlays().getArray()
  for (let i = overlays.length - 1; i >= 0; i--) {
    const overlay = overlays[i]
    const element = overlay.getElement()
    if (element && element.classList.contains('ol-tooltip-static')) {
      olMap.removeOverlay(overlay)
    }
  }

  if (activeMeasurementTool.value) {
    olMap.removeOverlay(measureTooltipOverlay)
    createMeasureTooltip()
  }
}

onMounted(() => {
  // 1. Inicjalizacja Mapy z przypisanymi zmiennymi min/max zoom
  olMap = new Map({
    target: mapContainer.value,
    view: new View({
      center: fromLonLat([16.8909, 50.9490]),
      zoom: 8,
      minZoom: MIN_ZOOM, // <-- Podpięta zmienna minimalnego zoomu
      maxZoom: MAX_ZOOM  // <-- Podpięta zmienna maksymalnego zoomu
    }),
    controls: [] 
  })

  // 2. Budowa warstw podkładowych
  olLayers['osm'] = new TileLayer({ source: new OSM(), visible: false, zIndex: 2 })
  olMap.addLayer(olLayers['osm'])
  
  olLayers['max_powodz_raster'] = new TileLayer({
    source: new TileWMS({
      url: '/geoserver/wms',
      params: { 'LAYERS': 'flood_ai:MaxZarejestrowanyZasiegPowodzi', 'TILED': true },
      serverType: 'geoserver',
    }),
    visible: false, zIndex: 1
  })
  olMap.addLayer(olLayers['max_powodz_raster'])

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
      zIndex: 10 
    })
    olMap.addLayer(olLayers[layer.id])
  })

  // 4. Inicjalizacja warstwy wektorowej dla POMIARÓW
  measureSource = new VectorSource()
  measureLayer = new VectorLayer({
    source: measureSource,
    style: new Style({
      fill: new Fill({ color: 'rgba(255, 255, 255, 0.2)' }),
      stroke: new Stroke({ color: '#ffcc33', width: 2 }),
      image: new CircleStyle({ radius: 7, fill: new Fill({ color: '#ffcc33' }) })
    }),
    zIndex: 9999
  })
  olMap.addLayer(measureLayer)

  // 5. Śledzenie kursora (W PUWG 1992 / EPSG:2180)
  olMap.on('pointermove', (evt) => {
    if (evt.dragging) return
    const coords2180 = transform(evt.coordinate, 'EPSG:3857', 'EPSG:2180')
    const x = coords2180[1].toFixed(2)
    const y = coords2180[0].toFixed(2)
    store.updateCoordinates(x, y) 
  })

  // 6. ZAPYTANIE GetFeatureInfo (Kliknięcie)
  olMap.on('singleclick', async (evt) => {
    if (activeMeasurementTool.value) return;

    if (!store.activeLayerId) {
      store.featureInfoHtml = '<p style="color: #cc0000; font-weight: bold;">Najpierw zaznacz warstwę na liście po lewej stronie.</p>'
      return
    }

    store.featureInfoHtml = '<p>Pobieranie atrybutów z bazy PostGIS...</p>'
    const activeLayer = olLayers[store.activeLayerId]
    
    if (!activeLayer) return;

    const viewResolution = olMap.getView().getResolution()
    
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

// Obserwatory (Watchers)
watch(() => store.baseMaps, (newBaseMaps) => {
  newBaseMaps.forEach(map => olLayers[map.id].setVisible(map.visible))
}, { deep: true })

watch(() => store.overlays, (newOverlays) => {
  newOverlays.forEach(layer => olLayers[layer.id].setVisible(layer.visible))
}, { deep: true })

watch(() => store.currentTimelapseDate, (newDate) => {
  if(olLayers['timelapse']) {
    olLayers['timelapse'].getSource().updateParams({ 'TIME': newDate })
  }
})

const zoom = (delta) => {
  if (!olMap) return
  const view = olMap.getView()
  // Animacja przybliżania/oddalania używająca Twoich przycisków +/- będzie teraz naturalnie blokowana
  // przez OpenLayers po osiągnięciu minZoom lub maxZoom.
  view.animate({ zoom: view.getZoom() + delta, duration: 250 })
}
</script>

<style scoped>
/* -------------------------------------
   STYLE DLA NAKŁADEK (TOOLTIPÓW) POMIARU
   ------------------------------------- */
.ol-tooltip {
  position: relative;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 4px;
  color: white;
  padding: 4px 8px;
  opacity: 0.7;
  white-space: nowrap;
  font-size: 12px;
  cursor: default;
  user-select: none;
}
.ol-tooltip-measure {
  opacity: 1;
  font-weight: bold;
}
.ol-tooltip-static {
  background-color: #004d26; /* Używamy Twojego głównego zielonego koloru */
  color: white;
  border: 1px solid white;
}
/* Tworzenie małej strzałki wskazującej w dół */
.ol-tooltip-measure:before,
.ol-tooltip-static:before {
  border-top: 6px solid rgba(0, 0, 0, 0.5);
  border-right: 6px solid transparent;
  border-left: 6px solid transparent;
  content: "";
  position: absolute;
  bottom: -6px;
  margin-left: -7px;
  left: 50%;
}
.ol-tooltip-static:before {
  border-top-color: #004d26;
}
</style>