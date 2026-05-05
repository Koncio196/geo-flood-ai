from langchain_core.tools import tool
from sqlalchemy import text
from database import SessionLocal

# --- KONFIGURACJA WARSTW GIS ---
GIS_LAYERS = {
    "budynki": {
        "table": "budynki",
        "function": {"funkcjaogolnabudynku": [
            "budynki biurowe",
            "budynki handlowo-usługowe",
            "budynki mieszkalne",
            "budynki oświaty, nauki i kultury oraz budynki sportowe",
            "budynki produkcyjne, usługowe i gospodarcze dla rolnictwa",
            "budynki przemysłowe",
            "budynki szpitali i inne budynki opieki zdrowotnej",
            "budynki transportu i łączności",
            "pozostałe budynki niemieszkalne",
            "zbiorniki, silosy i budynki magazynowe",
            ]},
        "geom_col": "geom"
    },
    "zasieg_powodzi": {
        "table": "zasieg_powodzi",
        "geom_col": "geom"
    },
    "obszar_zagrozenia_powodziowego_1": {
        "table": "obszar_zagrozenia_powodziowego_1",
        "geom_col": "geom"
    },
    "gminy": {
        "table": "gminy",
        "name_col": "nazwa",
        "geom_col": "geom"
    },
    "powiaty": {
        "table": "powiaty",
        "name_col": "nazwa",
        "geom_col": "geom"
    },
    "wojewodztwa": {
        "table": "wojewodztwa",
        "name_col": "nazwa",
        "geom_col": "geom"
    },
    
    "drogi": {
        "table": "drogi",
        "kategoria_zarzadzania": "kategoriazarzadzania",
        "placement": "polozenie",
        "geom_col": "geom"
    }
}

@tool
def get_building_count() -> dict:
    """
    Zwraca całkowitą liczbę budynków w bazie danych (tabela 'budynki'). 
    Używaj tylko wtedy, gdy użytkownik pyta o ogólną, całkowitą liczbę budynków w obu województwach.
    """
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT COUNT(*) FROM budynki;")).scalar()
        return {"status": "success", "total_buildings": result}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}
    finally:
        db.close()
        

@tool
def get_flooded_area_for_city(city_name: str) -> dict:
    """
    Zwraca surowe dane o powierzchni zalanego obszaru dla podanej miejscowości.
    """
    db = SessionLocal()
    try:
        query = text("""
            SELECT 
                g.nazwa,
                ROUND((ST_Area(ST_Intersection(g.geom, p.geom)) / 10000)::numeric, 2) AS zalana_pow_ha
            FROM gminy g
            JOIN zasieg_powodzi p ON ST_Intersects(g.geom, p.geom)
            WHERE g.nazwa ILIKE :city_name
            LIMIT 1;
        """)
        
        result = db.execute(query, {"city_name": f"%{city_name}%"}).fetchone()
        
        # Narzędzie zwraca SŁOWNIK (czyste dane), a nie gotowe zdanie!
        if result and result.zalana_pow_ha is not None:
            return {
                "status": "success",
                "city_matched": result.nazwa,
                "flooded_area_hectares": float(result.zalana_pow_ha)
            }
        else:
            return {
                "status": "not_found",
                "requested_city": city_name
            }
            
    except Exception as e:
        return {"status": "error", "error_message": str(e)}
    finally:
        db.close()
        
        
@tool
def get_buildings_risk_stats(analysis_type: str, city_name: str, building_function: str = None) -> dict:
    """
    Oblicza liczbę budynków w strefie dla konkretnej gminy. 
    Argumenty: 
    - analysis_type: 'current_flood' dla obszarów zalanych, dotkniętnych powodzią lub 'hazard_zone' dla obszarów zagrożonych, będących w strefie zagrożenia powodziowego
    - city_name: nazwa gminy (np. 'Wrocław')
    - building_function: opcjonalnie typ budynku
    """
    mapping = {
        "current_flood": "zasieg_powodzi",
        "hazard_zone": "obszar_zagrozenia_powodziowego_1"
    }

    if analysis_type not in mapping:
        return {"status": "error", "message": "Nieznany typ analizy."}

    target_table = GIS_LAYERS[mapping[analysis_type]]["table"]
    target_geom = GIS_LAYERS[mapping[analysis_type]]["geom_col"]
    
    # Dynamiczne pobranie kolumny funkcji (funkcjaogolnabudynku)
    func_col = list(GIS_LAYERS["budynki"]["function"].keys())[0]

    db = SessionLocal()
    try:
        # 1. Budowanie klauzuli filtra (gmina jest teraz wymagana dla wydajności)
        filter_clause = "AND g.nazwa ILIKE :city"
        params = {"city": f"{city_name}"}
        
        if building_function:
            filter_clause += f" AND b.{func_col} = :b_func"
            params["b_func"] = building_function

        # 2. Query z JOINem do gmin, żeby ograniczyć obszar przetwarzania
        query = text(f"""
            SELECT COUNT(b.geom) 
            FROM budynki b
            JOIN gminy g ON ST_Intersects(b.geom, g.geom)
            WHERE EXISTS (
                SELECT 1 
                FROM "{target_table}" t 
                WHERE ST_Intersects(b.geom, t.{target_geom})
                AND ST_Intersects(t.{target_geom}, g.geom)
            ) {filter_clause};
        """)
        
        result = db.execute(query, params).scalar()
        
        return {
            "status": "success",
            "count": result,
            "city": city_name,
            "details": f"Znaleziono {result} obiektów w gminie {city_name}."
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}
    finally:
        db.close()