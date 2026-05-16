import rasterio
import numpy as np
from skimage.filters import threshold_otsu
import geopandas as gpd

def prepare_val_dataset(vector_path: str, template_profile: dict) -> np.ndarray:
    """
    Wczytuje wektor z zasięgiem powodzi (Copernicus EMS) i "wypala" go na pustej 
    macierzy rastrowej, zachowując idealną zgodność z siatką pikseli i układem 
    współrzędnych Sentinela.
    
    Parametry:
    - vector_path: Ścieżka do pliku wektorowego z powodzią (np. .gpkg, .shp)
    - template_profile: Słownik metadanych pobrany z rastra bazowego (z rasterio)
    
    Zwraca:
    - validation_raster (np.ndarray): Binarna macierz 2D (1 = powódź, 0 = brak powodzi)
    """
    try:
        # 1. Wczytanie warstwy wektorowej
        gdf = gpd.read_file(vector_path)
        
        if gdf.empty:
            raise ValueError(f"Plik wektorowy {vector_path} jest pusty!")

        # 2. Inżynierska kontrola krzyżowa układów współrzędnych
        # Sprawdzamy, czy EPSG wektora zgadza się z EPSG szablonu (np. 2180)
        template_crs = template_profile['crs']
        if gdf.crs != template_crs:
            print(f"Ostrzeżenie: CRS wektora ({gdf.crs}) różni się od CRS szablonu ({template_crs}). Wymuszam reprojekcję w locie.")
            gdf = gdf.to_crs(template_crs)

        # 3. Ekstrakcja geometrii do formatu strawnego dla rasterio
        # Bierzemy tylko poprawne geometrie, ignorujemy ewentualne nulle
        geometries = [geom for geom in gdf.geometry if geom is not None]

        if not geometries:
            # Jeśli w danym AOI nie było wody według Copernicusa, zwracamy puste zera
            return np.zeros((template_profile['height'], template_profile['width']), dtype=np.uint8)

        # 4. Magia rasteryzacji
        # Wypalamy geometrie na macierzy o dokładnie takich samych wymiarach i 
        # transformacji affinicznej, jak nasz raster z Sentinela.
        validation_raster = features.rasterize(
            shapes=geometries,
            out_shape=(template_profile['height'], template_profile['width']),
            transform=template_profile['transform'],
            fill=0,             # Tło to 0 (brak wody)
            default_value=1,    # Wnętrze poligonu to 1 (woda)
            dtype=np.uint8      # Typ danych dbający o RAM i dysk
        )

        return validation_raster

    except Exception as e:
        print(f"Błąd podczas rasteryzacji warstwy walidacyjnej: {str(e)}")
        raise

def read_raster_data(file_path: str):
    """
    Wczytuje 4-kanałowy raster (GeoTIFF) wyeksportowany z GEE.
    Zwraca słownik z pasmami oraz metadane przestrzenne, niezbędne do późniejszego zapisu.
    """
    try:
        with rasterio.open(file_path) as src:
            # 1. Pobieramy metadane (transformacja affiniczna, układ współrzędnych, wymiary)
            # Kopia profilu jest nam niezbędna, żeby na końcu zapisać wynikowy raster powodzi 
            # dokładnie w tym samym miejscu na Ziemi.
            profile = src.profile

            # 2. Wczytujemy pasma z użyciem masked=True!
            # To sprawia, że rasterio zwraca tzw. Masked Arrays z Numpy.
            # Dzięki temu wartości NoData (czarne ramki) nie wezmą udziału w obliczeniach Otsu i ML.
            vv_flood = src.read(1, masked=True)
            vh_flood = src.read(2, masked=True)
            vv_diff  = src.read(3, masked=True)
            hand     = src.read(4, masked=True)
            
            # Pobieramy maskę (gdzie True oznacza prawidłowe dane, a False obszar NoData)
            # Pamiętaj, że wszystkie kanały mają taki sam zasięg danych, więc wystarczy maska z kanału 1.
            valid_data_mask = ~vv_flood.mask 

        # 3. Zwracamy SŁOWNIK, a nie zwykłą listę.
        # Dlaczego? Bo nie chcemy "magicznych numerów" (indeksów 0, 1, 2) w kodzie klasyfikatorów.
        # Od teraz do algorytmu podajemy po prostu raster_data['VH_flood'].
        raster_data = {
            'VV_flood': vv_flood,
            'VH_flood': vh_flood,
            'VV_diff': vv_diff,
            'HAND': hand,
            'valid_data_mask': valid_data_mask
        }

        return raster_data, profile

    except rasterio.errors.RasterioIOError:
        print(f"Błąd krytyczny: Nie można otworzyć pliku {file_path}. Sprawdź ścieżkę w kontenerze Docker.")
        raise
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd podczas wczytywania rastra: {str(e)}")
        raise

def apply_otsu_classification(band_data: np.ma.MaskedArray, valid_mask: np.ndarray) -> tuple:
    """
    Wyznacza próg Otsu na podanym paśmie radarowym i klasyfikuje piksele.
    
    Parametry:
    - band_data: Macierz z danymi radarowymi (np. VH_flood lub VV_diff).
    - valid_mask: Binarna maska oznaczająca poprawne piksele (bez NoData).
    
    Zwraca:
    - binary_flood (np.ndarray): Macierz 2D, gdzie 1 = woda, 0 = ląd/NoData.
    - threshold (float): Wyliczona wartość progu (do logów/pracy mgr).
    """
    # 1. Wyciągamy do histogramu TYLKO ważne piksele (1D array)
    # Gdybyśmy wrzucili całą macierz z NoData, Otsu znalazłby próg między NoData a resztą świata.
    valid_pixels = band_data[valid_mask]
    
    if len(valid_pixels) == 0:
        raise ValueError("Brak poprawnych pikseli do obliczenia progu Otsu.")
        
    # 2. Obliczamy próg Otsu na czystych danych
    threshold = threshold_otsu(valid_pixels)
    
    # 3. Inicjalizujemy pustą macierz wynikową zerami (0 = ląd)
    binary_flood = np.zeros_like(band_data, dtype=np.uint8)
    
    # 4. KLUCZOWA LOGIKA FIZYCZNA:
    # Woda to gładka powierzchnia -> niskie wsteczne rozproszenie sygnału -> wartości < próg.
    # Aplikujemy tę logikę tylko na poprawnych pikselach (dzięki valid_mask czarne trójkąty na rogach zostają zerami).
    binary_flood[valid_mask] = (band_data[valid_mask] < threshold).astype(np.uint8)
    
    return binary_flood, threshold


#==================
# Wywołanie funkcji
#==================
# KROK 1: Wczytanie danych z radaru (nasz szablon i predyktory)
raster_dict, profile = read_raster_data("S1_Flood_Stack_10m.tif")

# KROK 2: Przygotowanie warstwy referencyjnej (Copernicus EMS) na bazie profilu
val_dataset = prepare_val_dataset("copernicus_ems_nysa.gpkg", profile)

# KROK 3: Klasyfikacja (np. Otsu na paśmie różnicowym)
diff_flood_mask, diff_thresh = apply_otsu_classification(
    band_data=raster_dict['VV_diff'], 
    valid_mask=raster_dict['valid_data_mask']
)

# W tym momencie masz w pamięci RAM dwie idealnie nakładające się na siebie 
# macierze binarne: diff_flood_mask (Twój wynik) oraz val_dataset (Prawda).