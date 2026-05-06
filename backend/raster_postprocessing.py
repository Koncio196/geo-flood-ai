import os
import re
from datetime import datetime
import numpy as np
import rasterio
from rasterio.features import sieve, shapes
import geopandas as gpd
from shapely.geometry import shape
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 1. BEZPIECZEŃSTWO: Ładowanie zmiennych z pliku .env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DB_USER = os.getenv("POSTGRES_USER", "admin")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "admin123")
DB_NAME = os.getenv("POSTGRES_DB", "flood_db")

# 2. AUTO-DETEKCJA ŚRODOWISKA (Docker vs Lokalny WSL)
DOCKER_DIR = '/app/raster_data/timelapse_rasters'

if os.path.exists('/app'):
    # Tryb DOCKER
    print("🐳 Wykryto środowisko Docker. Używam wewnętrznej sieci.")
    DB_HOST = "postgres_db"
    DB_PORT = "5432"
    RASTER_DIR = DOCKER_DIR
else:
    # Tryb LOKALNY (WSL)
    print("💻 Wykryto środowisko lokalne. Używam localhost.")
    DB_HOST = "localhost"
    DB_PORT = "5434"
    RASTER_DIR = os.path.join(os.path.dirname(__file__), '..', 'raster_data', 'timelapse_rasters')

# Budowa URL połączenia (SQLAlchemy)
DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def init_db_table(engine):
    """Tworzy zoptymalizowaną tabelę docelową, jeśli nie istnieje."""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS flood_polygons (
        id SERIAL PRIMARY KEY,
        acquisition_date DATE NOT NULL,
        area_sqm DOUBLE PRECISION,
        geom GEOMETRY(MultiPolygon, 2180)
    );
    CREATE INDEX IF NOT EXISTS sidx_flood_polygons_geom ON flood_polygons USING GIST (geom);
    CREATE INDEX IF NOT EXISTS idx_flood_polygons_date ON flood_polygons (acquisition_date);
    """
    with engine.begin() as conn:
        conn.execute(text(create_table_sql))
    print("✓ Tabela bazodanowa flood_polygons jest gotowa.")

def process_rasters():
    engine = create_engine(DB_URL)
    init_db_table(engine)
    
    # Wyrażenie regularne do szukania daty RRRR-MM-DD w nazwie pliku
    date_pattern = re.compile(r"(\d{4}-\d{2}-\d{2})_clip\.tif$")

    for filename in os.listdir(RASTER_DIR):
        match = date_pattern.search(filename)
        if not match:
            continue
        
        date_str = match.group(1)
        acq_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        filepath = os.path.join(RASTER_DIR, filename)

        # 2. IDEMPOTENTNOŚĆ: Sprawdź, czy ta data już jest w bazie
        with engine.connect() as conn:
            check_sql = text("SELECT 1 FROM flood_polygons WHERE acquisition_date = :d LIMIT 1")
            result = conn.execute(check_sql, {"d": acq_date}).fetchone()
            if result:
                print(f"⏩ Pomijam {filename} - dane z {acq_date} już są w bazie.")
                continue

        print(f"⏳ Przetwarzanie rastra dla daty {acq_date}...")

        # 3. Wczytywanie i progowanie
        with rasterio.open(filepath) as src:
            # Upewniamy się, że czytamy poprawne EPSG
            if src.crs.to_epsg() != 3857:
                print(f"⚠️ UWAGA: Plik {filename} ma CRS {src.crs}, a oczekiwano EPSG:3857!")
            
            raster_data = src.read(1) # Czytanie pierwszego pasma
            
            # Tworzenie maski binarnej (woda to 1 dla wartości < -18)
            binary_mask = np.where(raster_data < -18, 1, 0).astype(rasterio.uint8)

            # 4. ODSZUMIANIE (Sieve)
            # Usuwamy "kałuże" mniejsze niż np. 10 pikseli. 
            # W EPSG:3857 przy Sentinelu to około 1000m2. Zapobiegnie to obciążeniu bazy.
            clean_mask = sieve(binary_mask, size=10, connectivity=4)

            # 5. WEKTORYZACJA (Tylko poligony wody: mask=(clean_mask == 1))
            geometries = []
            for geom, value in shapes(clean_mask, mask=(clean_mask == 1), transform=src.transform):
                geometries.append(shape(geom))

        if not geometries:
            print(f"⚠️ Brak wody na zdjęciu z {acq_date}.")
            continue

        # 6. Transformacja EPSG i ładowanie do DB
        # Tworzymy GeoDataFrame
        gdf = gpd.GeoDataFrame({'acquisition_date': acq_date}, geometry=geometries, crs="EPSG:3857")
        
        # Zmiana układu na PL-1992 (EPSG:2180)
        gdf = gdf.to_crs(epsg=2180)
        
        # Obliczenie powierzchni dla analityki Agenta
        gdf['area_sqm'] = gdf.geometry.area
        
        # Rozwiązanie problemu złożonych poligonów - upewniamy się, że mamy MultiPoligony
        gdf.geometry = gdf.geometry.apply(
            lambda g: g if g.geom_type == 'MultiPolygon' else gpd.GeoSeries([g]).explode(index_parts=False).unary_union
        )
        # Wymuszamy MultiPolygon w typie (dla bazy PostGIS)
        gdf['geometry'] = [g if g.geom_type == 'MultiPolygon' else gpd.GeoSeries([g]).explode(index_parts=False).unary_union for g in gdf.geometry]
        gdf = gdf.set_geometry('geometry')

        # 7. Zapis do bazy danych
        print(f"💾 Zapisywanie {len(gdf)} poligonów wody do bazy (EPSG:2180)...")
        gdf.to_postgis(
            name='flood_polygons', 
            con=engine, 
            if_exists='append', 
            index=False
        )
        print(f"✅ Zakończono przetwarzanie dla {acq_date}.")

if __name__ == "__main__":
    process_rasters()