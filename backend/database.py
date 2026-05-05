import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Pobieranie zmiennych środowiskowych wstrzykniętych przez Dockera
USER = os.environ['CHATBOT_USER']
PASSWORD = os.environ['CHATBOT_PASSWORD']
DB = os.environ['POSTGRES_DB']

# Połączenie
DATABASE_URL = f"postgresql://{USER}:{PASSWORD}@postgres_db:5432/{DB}"

# 2. Inicjalizacja silnika SQLAlchemy
# pool_pre_ping=True to świetna praktyka - sprawdza czy połączenie nie wygasło przed wykonaniem zapytania
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# 3. Fabryka sesji do komunikacji z bazą
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Klasa bazowa dla przyszłych modeli ORM (jeśli będziesz chciał mapować tabele na obiekty Pythona)
Base = declarative_base()

def get_db():
    """
    Generator sesji bazy danych. Będzie używany przez narzędzia Agenta
    do bezpiecznego otwierania i zamykania połączeń.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()