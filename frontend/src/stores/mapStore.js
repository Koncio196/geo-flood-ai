import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useMapStore = defineStore('map', () => {
  // Stan UI
  const isSidebarOpen = ref(true)
  const coordinates = ref({ lat: '--', lon: '--' })
  
  // Stan Mapy
  const activeLayerId = ref(null) 
  const featureInfoHtml = ref('<p style="color: #666; font-style: italic; font-size: 13px;">Kliknij obiekt na mapie, aby pobrać atrybuty z bazy PostGIS.</p>')
  
  // Szereg czasowy
  const timelapseDates = [
    '2024-09-10', '2024-09-11', '2024-09-13', '2024-09-15', '2024-09-16', 
    '2024-09-18', '2024-09-20', '2024-09-22', '2024-09-23', '2024-09-25', 
    '2024-09-27', '2024-09-28', '2024-09-30', '2024-10-02'
  ]
  const currentTimelapseIndex = ref(0)
  const currentTimelapseDate = computed(() => timelapseDates[currentTimelapseIndex.value])

  // --- ZMIANA 1: Definicja Podkładów (Kolejność: OSM -> Sentinel -> Ortofoto) ---
  const baseMaps = ref([
    { id: 'osm', name: 'Open Street Map', visible: false, isBase: true },
    { id: 'max_powodz_raster', name: 'Mozaika wartości minimalnej Sentinel-1', layerName: 'flood_ai:MaxZarejestrowanyZasiegPowodzi', visible: false, isBase: true },
    { id: 'ortofoto', name: 'Ortofotomapa Standardowa GUGiK', layerName: 'flood_ai:ORTOFOTOMAPA', visible: false, isBase: true }
  ])

  // Warstwy (Zwróć uwagę, że usunąłem stąd max_powodz_raster)
  const overlays = ref([
    { id: 'wojewodztwa', name: 'Województwa', layerName: 'flood_ai:wojewodztwa', visible: true },
    { id: 'powiaty', name: 'Powiaty', layerName: 'flood_ai:powiaty', visible: true },
    { id: 'gminy', name: 'Gminy', layerName: 'flood_ai:gminy', visible: true },
    { id: 'budynki', name: 'Budynki', layerName: 'flood_ai:budynki', visible: true },
    { id: 'drogi', name: 'Drogi', layerName: 'flood_ai:drogi', visible: false },
    { id: 'ozp_1', name: 'Obszar zagrożenia powodziowego 1%', layerName: 'flood_ai:obszar_zagrozenia_powodziowego_1', visible: false },
    { id: 'cems', name: 'CEMS - Rapid Mapping', layerName: 'flood_ai:copernicus_flood_area', visible: false },
    { id: 'max_powodz', name: 'Maksymalny Zaobserowany Zasięg Powodzi', layerName: 'flood_ai:maksymalny_zasieg_powodzi', visible: false },
    { id: 'timelapse', name: 'Rastry Zasięgu Powodzi (Szereg Czasowy)', layerName: 'flood_ai:timelapse_rasters', visible: false, isTimelapse: true }
  ])

  // Akcje
  const toggleSidebar = () => isSidebarOpen.value = !isSidebarOpen.value
  const updateCoordinates = (lat, lon) => coordinates.value = { lat, lon }
  
  const toggleLayerVisibility = (layerId, isBaseMap = false) => {
    if (isBaseMap) {
      const layer = baseMaps.value.find(l => l.id === layerId)
      if (layer) {
        // --- ZMIANA 2: Logika MAX 1 podkład ---
        const willBeVisible = !layer.visible;
        
        // Jeśli WŁĄCZAMY dany podkład, najpierw wyłączamy wszystkie pozostałe
        if (willBeVisible) {
          baseMaps.value.forEach(m => m.visible = false);
        }
        
        // Następnie nadajemy nowy stan klikniętemu podkładowi
        layer.visible = willBeVisible;
      }
    } else {
      const layer = overlays.value.find(l => l.id === layerId)
      if (layer) layer.visible = !layer.visible
    }
  }

  const setActiveQueryLayer = (layerId) => {
    if (activeLayerId.value === layerId) {
      activeLayerId.value = null // Odklikiwanie
      featureInfoHtml.value = '<p style="color: #666; font-style: italic; font-size: 13px;">Kliknij obiekt na mapie, aby pobrać atrybuty z bazy PostGIS.</p>'
    } else {
      activeLayerId.value = layerId // Zaznaczanie
      // ZMIANA: Szukamy warstwy zarówno w nakładkach, jak i w podkładach (by można było odpytać Sentinela)
      const layer = overlays.value.find(l => l.id === layerId) || baseMaps.value.find(l => l.id === layerId)
      featureInfoHtml.value = `<p style="color: #004d26; font-weight: bold;">Aktywna warstwa: ${layer.name}</p>
                               <p style="color: #666; font-style: italic; font-size: 13px;">Kliknij w obiekt na mapie, aby pobrać atrybuty.</p>`
    }
  }

  return {
    isSidebarOpen, coordinates, activeLayerId, featureInfoHtml,
    timelapseDates, currentTimelapseIndex, currentTimelapseDate,
    baseMaps, overlays,
    toggleSidebar, updateCoordinates, toggleLayerVisibility, setActiveQueryLayer
  }
})