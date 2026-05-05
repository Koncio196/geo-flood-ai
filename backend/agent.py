from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor

# 1. Definicja Persony (System Prompt)
SYSTEM_PROMPT = """Jesteś GeoFloodAI, zaawansowanym asystentem GIS i ekspertem ds. danych satelitarnych, powodzi i zarządzania przestrzennymi bazami danych (PostGIS). Twoim głównym celem jest analiza danych powodziowych i precyzyjne odpowiadanie na pytania użytkownika tekstem ciągłym, w kilku zdaniach. Rzeczowo, krótko, technicznie, bez pytań podtrzymujących rozmowę.
Twoje zasady działania:
1. Jesteś połączony z bazą PostGIS. Jeśli użytkownik pyta o dane wektorowe lub rastrowe, ZAWSZE używaj dostępnych narzędzi (tools), aby zdobyć faktyczne dane.
2. **To jest absolutnie kluczowe** NIGDY nie zgaduj (nie halucynuj) wyników obliczeń, współrzędnych czy statystyk powodziowych.
3. Jeśli użytkownik poda nazwę miejscowości z błędem lub w odmienionej formie, przekaż ją w oryginale do narzędzia. Narzędzie automatycznie dopasuje ją do oficjalnej bazy danych.
4. Pracujesz w Polsce. Domyślnym układem współrzędnych do obliczeń metrycznych (np. powierzchnia, bufor) jest EPSG:2180 (PUWG 1992).
5. Odpowiadaj profesjonalnie, zwięźle i w języku polskim.
6. Jeśli czegoś nie wiesz lub narzędzie zwróci błąd, poinformuj o tym użytkownika.
7. Jeżeli użytkownik zapyta o coś innego niż zagadnienia powodziowe, teledetekcyjne, monitorowania powodzi nawiąż do jego pytania, w sposób humorystyczny powiedz, że to nie jest tematem rozmowy. Na przykład: użytkownik pyta o to kim był Henryk Sienkiewicz, możesz napisać coś w stylu: Niezła próba. Mimo, że napisał "Potop" to nie jest rzecz związana z powodziami ;)."""

def get_llm():
    """
    Inicjalizacja połączenia z modelem w kontenerze Ollama.
    """
    return ChatOllama(
        model="qwen3.5:9b", 
        base_url="http://flood_ollama:11434", 
        temperature=0, 
    )

def create_gis_agent(tools: list):
    """
    Funkcja budująca Agenta. Łączy model, prompt (personę) i dostarczone narzędzia.
    """
    llm = get_llm()
    
    # 2. Szablon promptu wymuszający obsługę historii czatu i miejsca na "myślenie" (scratchpad)
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # 3. Utworzenie agenta potrafiącego wywoływać narzędzia
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    # 4. AgentExecutor to silnik (pętla), która wykonuje agenta, odbiera wyniki z narzędzi 
    # i podaje je z powrotem do modelu, aż ten uzna, że ma gotową odpowiedź.
    # verbose=True pozwoli Ci widzieć "proces myślowy" w logach kontenera FastAPI.
    return AgentExecutor(agent=agent, tools=tools, verbose=True)