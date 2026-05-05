// 1. INICJALIZACJA MAPY
const map = L.map('map', {
    center: [50.67, 17.02], 
    zoom: 8, 
    zoomControl: false 
});

L.control.scale({
    metric: true,
    imperial: false,
    position: 'bottomright'
}).addTo(map);

// 2. MAPY PODKŁADOWE
const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    zIndex: 1
});

const ortofoto = L.tileLayer.wms('/geoserver/wms', {
    layers: 'flood_ai:ORTOFOTOMAPA', 
    format: 'image/png',
    transparent: true,
    version: '1.1.1',
    attribution: '&copy; <a href="https://www.geoportal.gov.pl">GUGiK</a>',
    zIndex: 0
});

// 3. WARSTWY Z GEOSERVERA
const budynki = L.tileLayer.wms('/geoserver/wms', {
    layers: 'flood_ai:budynki', 
    format: 'image/png',
    transparent: true,
    version: '1.1.1',
    zIndex: 20
});

const drogi = L.tileLayer.wms('/geoserver/wms', {
    layers: 'flood_ai:drogi', 
    format: 'image/png',
    transparent: true,
    version: '1.1.1',
    zIndex: 19
});

const wojewodztwa = L.tileLayer.wms('/geoserver/wms', {
    layers: 'flood_ai:wojewodztwa', 
    format: 'image/png',
    transparent: true,
    version: '1.1.1',
    zIndex: 10
}).addTo(map); 

const powiaty = L.tileLayer.wms('/geoserver/wms', {
    layers: 'flood_ai:powiaty', 
    format: 'image/png',
    transparent: true,
    version: '1.1.1',
    zIndex: 10
}).addTo(map);

const gminy = L.tileLayer.wms('/geoserver/wms', {
    layers: 'flood_ai:gminy', 
    format: 'image/png',
    transparent: true,
    version: '1.1.1',
    zIndex: 10
}).addTo(map);

const max_powodz = L.tileLayer.wms('/geoserver/wms', {
    layers: 'flood_ai:maksymalny_zasieg_powodzi', 
    format: 'image/png',
    transparent: true,
    version: '1.1.1',
    zIndex: 4
}).addTo(map);

const ozp_1 = L.tileLayer.wms('/geoserver/wms', {
    layers: 'flood_ai:obszar_zagrozenia_powodziowego_1', 
    format: 'image/png',
    transparent: true,
    version: '1.1.1',
    zIndex: 3
}).addTo(map);

const max_powodz_raster = L.tileLayer.wms('/geoserver/wms', {
    layers: 'flood_ai:MaxZarejestrowanyZasiegPowodzi', 
    format: 'image/png',
    transparent: true,
    version: '1.1.1',
    zIndex: 2
}).addTo(map);

// Zmienna globalna trzymająca aktywną warstwę do odpytywania
let activeQueryLayer = null;

// 4. INTEGRACJA Z TWOIM LEWYM PANELEM
const baseMaps = [
    { name: "Open Street Map", layer: osmLayer, active: false },
    { name: "Ortofotomapa Standardowa  GUGiK", layer: ortofoto, active: false }
];

// 2. Funkcja budująca listę podkładów w panelu bocznym
function renderBaseMaps() {
    const mapListContainer = document.getElementById('map-list');
    mapListContainer.innerHTML = ''; // Czyszczenie kontenera

    baseMaps.forEach((baseMap) => {
        // Główny kontener elementu (wykorzystuje Twoje style CSS)
        const itemDiv = document.createElement('div');
        itemDiv.className = 'layer-item';

        // Etykieta z nazwą mapy
        const label = document.createElement('span');
        label.className = 'layer-label';
        label.textContent = baseMap.name;

        // Kontener na przełącznik (switch)
        const switchLabel = document.createElement('label');
        switchLabel.className = 'switch';

        // Sam checkbox
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = baseMap.active;

        // Graficzny suwak
        const slider = document.createElement('span');
        slider.className = 'slider';

        // Poskładanie elementów w całość
        switchLabel.appendChild(checkbox);
        switchLabel.appendChild(slider);
        
        itemDiv.appendChild(label);
        itemDiv.appendChild(switchLabel);

        // 3. Logika włączania/wyłączania podkładu
        checkbox.addEventListener('change', (e) => {
            const isChecked = e.target.checked;
            baseMap.active = isChecked;
            
            if (isChecked) {
                map.addLayer(baseMap.layer);
            } else {
                map.removeLayer(baseMap.layer);
            }
        });

        // Dodanie do lewego panelu
        mapListContainer.appendChild(itemDiv);
    });
}

// 4. Uruchomienie funkcji po załadowaniu skryptu
renderBaseMaps();

const overlays = [
    { name: "Województwa", layer: wojewodztwa, active: true},
    { name: "Powiaty", layer: powiaty, active: true},
    { name: "Gminy", layer: gminy, active: true},
	{ name: "Budynki", layer: budynki, active: false},
    { name: "Drogi", layer: drogi, active: false},
    { name: "Obszar zagrożenia powodziowego 1%", layer: ozp_1, active: false},
    { name: "Maksymalny Zaobserowany Zasięg Powodzi [10-09-2024 - 03-10-2024]", layer: max_powodz, active: true},
    { name: "Mozaika wartości minimalnej Sentinel-1 [10-09-2024 - 03-10-2024]", layer: max_powodz_raster, active: false}
];

const layerListDiv = document.getElementById('layer-list');

overlays.forEach(item => {
    const div = document.createElement('div');
    div.className = 'layer-item';

    div.innerHTML = `
        <label class="switch">
            <input type="checkbox" ${item.active ? 'checked' : ''}>
            <span class="slider"></span>
        </label>
        <span class="layer-label">${item.name}</span>
    `;

    // A) LOGIKA WŁĄCZANIA/WYŁĄCZANIA WARSTWY NA MAPIE
    const checkbox = div.querySelector('input');
    checkbox.addEventListener('change', function(e) {
        if (this.checked) map.addLayer(item.layer);
        else map.removeLayer(item.layer);
    });

    // B) LOGIKA ZAZNACZANIA AKTYWNEJ WARSTWY (QGIS Style)
    div.addEventListener('click', function(e) {
        // Ignoruj kliknięcie, jeśli użytkownik kliknął tylko w sam włącznik (żeby nie zmieniać wyboru)
        if (e.target.closest('.switch')) return;

        // Usuń klasę 'selected' ze wszystkich elementów
        document.querySelectorAll('.layer-item').forEach(el => el.classList.remove('selected'));
        
        // Dodaj klasę do klikniętego
        div.classList.add('selected');
        
        // Ustaw aktywną warstwę w pamięci
        activeQueryLayer = item.layer;
        
        // Wyczyść panel z poprzednich informacji
        document.getElementById('feature-info').innerHTML = 
            `<p style="color: #004d26; font-weight: bold;">Aktywna warstwa: ${item.name}</p>
             <p style="color: #666; font-style: italic; font-size: 13px;">Kliknij w obiekt na mapie, aby pobrać atrybuty.</p>`;
    });

    layerListDiv.appendChild(div);
});

// 5. ZAPYTANIA O ATRYBUTY (GetFeatureInfo po kliknięciu w mapę)
map.on('click', function(e) {
    const infoPanel = document.getElementById('feature-info');

    // Jeśli użytkownik nie "zaklikał" żadnej warstwy na zielono po lewej stronie
    if (!activeQueryLayer) {
        infoPanel.innerHTML = '<p style="color: #cc0000; font-weight: bold;">Najpierw zaznacz warstwę na liście po lewej stronie (kliknij w jej tło/nazwę), aby ją odpytać.</p>';
        return;
    }

    // Pobranie nazwy roboczej warstwy z GeoServera
    const layerName = activeQueryLayer.options.layers;

    // Przeliczenie pikseli i BBOX do wymogów protokołu WMS
    const point = map.latLngToContainerPoint(e.latlng, map.getZoom());
    const size = map.getSize();
    const bounds = map.getBounds();
    const sw = map.options.crs.project(bounds.getSouthWest());
    const ne = map.options.crs.project(bounds.getNorthEast());
    const bbox = `${sw.x},${sw.y},${ne.x},${ne.y}`;

    infoPanel.innerHTML = '<p>Pobieranie atrybutów z bazy PostGIS...</p>';

    // Budowa URL do GeoServera (Wymuszamy format JSON, aby łatwo zbudować tabelkę)
    const url = `/geoserver/wms?request=GetFeatureInfo&service=WMS&srs=EPSG:3857&styles=&transparent=true&version=1.1.1&format=image/png&bbox=${bbox}&height=${size.y}&width=${size.x}&layers=${layerName}&query_layers=${layerName}&info_format=application/json&x=${Math.round(point.x)}&y=${Math.round(point.y)}`;

    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.features && data.features.length > 0) {
                const props = data.features[0].properties;
                let tableHtml = '<table><tr><th>Atrybut</th><th>Wartość</th></tr>';
                for (const key in props) {
                    tableHtml += `<tr><td><strong>${key}</strong></td><td>${props[key]}</td></tr>`;
                }
                tableHtml += '</table>';
                infoPanel.innerHTML = tableHtml;
            } else {
                infoPanel.innerHTML = '<p>Brak obiektów w klikniętym miejscu na tej warstwie.</p>';
            }
        })
        .catch(err => {
            console.error(err);
            infoPanel.innerHTML = '<p style="color: red;">Błąd komunikacji z GeoServerem. Sprawdź logi w konsoli.</p>';
        });
});

// 6. OBSŁUGA INTERFEJSU (Przyciski na mapie)
window.adjustZoom = function(direction) {
    if (direction > 0) map.zoomIn();
    else map.zoomOut();
};

document.getElementById('btn-sidebar-toggle').addEventListener('click', function() {
    const container = document.querySelector('.container');
    container.classList.toggle('sidebar-closed');
    setTimeout(() => map.invalidateSize(), 300);
});

window.clearMeasurements = function() {
    console.log("Czyszczenie pomiarów...");
};

// 7. AKTUALIZACJA WSPÓŁRZĘDNYCH KURSORA NA PASKU
const coordsDiv = document.getElementById('mouse-coords');

map.on('mousemove', function(e) {
    const lat = e.latlng.lat.toFixed(4);
    const lng = e.latlng.lng.toFixed(4);
    coordsDiv.innerHTML = `N: ${lat}°, E: ${lng}°`;
});

map.on('mouseout', function() {
    coordsDiv.innerHTML = `N: --, E: --`;
});

// ==========================================
// 8. OBSŁUGA ASYSTENTA AI (Chatbot)
// ==========================================

const chatInput = document.getElementById('chat-input');
const btnSendChat = document.getElementById('btn-send-chat');
const chatMessages = document.getElementById('chat-messages');

// Funkcja pomocnicza do dodawania dymków czatu
function appendMessage(text, senderClass, id = null) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${senderClass}`; // 'ai-message' lub 'user-message'
    
    // Jeśli wiadomość to HTML (np. tabela lub pogrubienia z Markdown), 
    // dla bezpieczeństwa w komercyjnych projektach używamy DOMPurify, 
    // ale na lokalne potrzeby pracy mgr wystarczy innerHTML
    msgDiv.innerHTML = text.replace(/\n/g, '<br>'); 
    
    if (id) msgDiv.id = id;
    
    // Ustawienie stylów dla wiadomości użytkownika (wyrównanie do prawej)
    if (senderClass === 'user-message') {
        msgDiv.style.backgroundColor = '#d1e7dd';
        msgDiv.style.color = '#0f5132';
        msgDiv.style.marginLeft = 'auto';
        msgDiv.style.marginRight = '10px';
        msgDiv.style.border = '1px solid #badbcc';
    }

    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight; // Auto-scroll w dół
}

// Główna funkcja wysyłająca zapytanie
async function sendMessage() {
    const messageText = chatInput.value.trim();
    if (!messageText) return;

    // 1. Pokaż wiadomość użytkownika i wyczyść pole
    appendMessage(messageText, 'user-message');
    chatInput.value = '';

    // 2. Pokaż tymczasowy status ładowania
    const loadingId = 'loading-' + Date.now();
    appendMessage('<i>Generowanie odpowiedzi...</i>', 'ai-message', loadingId);

    try {
        // 3. Wysłanie POST do Nginxa (który przekaże to do FastAPI)
        const response = await fetch('api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: messageText })
        });

        const data = await response.json();
        
        // 4. Usunięcie komunikatu "Agent analizuje..."
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();

        // 5. Wyświetlenie odpowiedzi od LLM lub komunikatu o błędzie
        if (data.status === 'success') {
            appendMessage(data.response, 'ai-message');
        } else {
            appendMessage(`<b>Błąd:</b> ${data.message}`, 'ai-message');
        }
    } catch (error) {
        document.getElementById(loadingId).remove();
        appendMessage('<b>Błąd krytyczny:</b> Brak połączenia z serwerem.', 'ai-message');
        console.error('Błąd komunikacji z API:', error);
    }
}

// Podpięcie akcji pod przycisk "Wyślij"
btnSendChat.addEventListener('click', sendMessage);

// Podpięcie akcji pod klawisz "Enter" (bez wciśniętego Shift)
chatInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault(); // Zapobiega przejściu do nowej linii
        sendMessage();
    }
});