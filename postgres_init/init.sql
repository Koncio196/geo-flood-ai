-- 1. Włączenie wsparcia dla PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_raster;
-- Do obsługi literówek i podobieństwa tekstu
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 2. Konfiguracja uprawnień dla ai_user
-- Najpierw upewniamy się, że ai_user ma dostęp do schematu
GRANT USAGE ON SCHEMA public TO ai_user;

-- Dajemy uprawnienia do odczytu wszystkich obecnych tabel
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ai_user;

-- Zapewniamy, że ai_user zobaczy tabele dodane w przyszłości
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO ai_user;

-- 3. Optymalizacja (Indeksy przestrzenne)
CREATE INDEX IF NOT EXISTS sidx_budynki_geom ON budynki USING GIST (geom);
CREATE INDEX IF NOT EXISTS sidx_drogi_geom ON drogi USING GIST (geom);
CREATE INDEX IF NOT EXISTS sidx_gminy_geom ON gminy USING GIST (geom);
CREATE INDEX IF NOT EXISTS sidx_zagrozenie_geom ON obszar_zagrozenia_powodziowego_1 USING GIST (geom);
CREATE INDEX IF NOT EXISTS sidx_zasieg_geom ON zasieg_powodzi USING GIST (geom);

-- 4. Statystyki dla planisty zapytań
ANALYZE budynki;
ANALYZE gminy;
ANALYZE drogi;
ANALYZE obszar_zagrozenia_powodziowego_1;
ANALYZE zasieg_powodzi;