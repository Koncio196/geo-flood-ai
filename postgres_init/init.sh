#!/bin/bash
# Zatrzymuje skrypt w przypadku jakiegokolwiek błędu
set -e

# Informacja w logach Dockera
echo "Rozpoczynam inicjalizację bazy danych i tworzenie ról..."

# psql łączy się z bazą używając domyślnych zmiennych roota z dockera
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
        -- 1. Włączenie wsparcia dla PostGIS
        CREATE EXTENSION IF NOT EXISTS postgis;
        CREATE EXTENSION IF NOT EXISTS postgis_raster;
        -- Do obsługi literówek i podobieństwa tekstu
        CREATE EXTENSION IF NOT EXISTS pg_trgm;

        -- 2. Konfiguracja uprawnień dla chatbota
        -- NAJPIERW TWORZYMY UŻYTKOWNIKA 
        CREATE USER $CHATBOT_USER WITH PASSWORD '$CHATBOT_PASSWORD';

        -- Następnie upewniamy się, że ma dostęp do schematu
        GRANT USAGE ON SCHEMA public TO $CHATBOT_USER;

        -- Dajemy uprawnienia do odczytu wszystkich obecnych tabel
        GRANT SELECT ON ALL TABLES IN SCHEMA public TO $CHATBOT_USER;

        -- Zapewniamy, że zobaczy tabele dodane w przyszłości
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO $CHATBOT_USER;
EOSQL

echo "Inicjalizacja bazy zakończona sukcesem!"