from fastapi import FastAPI
from pydantic import BaseModel
from agent import create_gis_agent
from tools.sql_tools import get_building_count, get_flooded_area_for_city, get_buildings_risk_stats

app = FastAPI(title="GeoFloodAI Backend")

# 1. Definicja struktury danych przychodzących z frontendu (JSON)
class ChatRequest(BaseModel):
    message: str

# 2. Inicjalizacja Agenta z listą dostępnych narzędzi
# Gdy napiszesz nowe narzędzia w przyszłości, po prostu dodasz je do tej listy
tools_list = [
    get_building_count,
    get_flooded_area_for_city,
    get_buildings_risk_stats
    ]

agent_executor = create_gis_agent(tools=tools_list)

@app.get("/")
def read_root():
    return {"message": "System GeoFloodAI jest online!"}

# 3. Główny endpoint czatu (Odbiera wiadomości typu POST)
@app.post("/chat")
def chat_with_agent(request: ChatRequest):
    try:
        # Uruchomienie Agenta LangChain z wiadomością od użytkownika
        response = agent_executor.invoke({"input": request.message})
        
        # Zwracamy wynik wygenerowany przez Qwena
        return {
            "status": "success", 
            "response": response["output"]
        }
    except Exception as e:
        # Obsługa błędów (np. gdyby padł kontener z Ollamą)
        return {
            "status": "error", 
            "message": str(e)
        }