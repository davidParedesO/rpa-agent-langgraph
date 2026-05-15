# Practica RPA + RAG con LangGraph

Proyecto de la practica de RPA. Consiste en un agente inteligente que registra equipamiento IT en un formulario web de forma automatica a partir de una peticion en lenguaje natural.

## Como funciona

El usuario escribe algo como "da de alta un monitor a 150 euros" y el agente:
1. Busca en ChromaDB el workflow correcto (search_procedures)
2. Extrae los parametros de la frase (extract_parameters)
3. Pide confirmacion antes de ejecutar (Human-in-the-Loop con interrupt de LangGraph)
4. Si el usuario confirma, Playwright rellena el formulario automaticamente (run_workflow)

## Arquitectura del agente y sus tools

```
Usuario (MAUI Blazor)
        |
        | HTTP POST /chat
        v
  FastAPI (api.py)
        |
        v
  Agente LangGraph (create_react_agent)
        |
        |-- search_procedures  --> ChromaDB (busqueda semantica del workflow)
        |-- extract_parameters --> LLM local (extrae datos de la peticion)
        |-- run_workflow        --> Playwright (automatiza el formulario web)
        |-- list_procedures    --> procedures/ (lista workflows disponibles)
```

El agente decide por si mismo que tools usar y en que orden. No hay ninguna logica de orquestacion escrita a mano.

## Por que LangGraph y no LangChain clasico

Use LangGraph (create_react_agent) en vez de LangChain clasico por dos razones principales:

- **Memoria entre turnos**: con MemorySaver y un thread_id fijo, el agente recuerda el contexto de la conversacion. Esto hace posible un chat real multi-turno donde el usuario puede referirse a lo que dijo antes.
- **Human-in-the-Loop**: LangGraph tiene soporte nativo para pausar el grafo con interrupt() y esperar una respuesta del usuario antes de ejecutar una accion critica. Con LangChain clasico habria que implementarlo a mano, lo que complicaria mucho el codigo.

## Trazas del agente

Cuando la API esta corriendo, en la consola de uvicorn se ven en tiempo real todas las llamadas a tools que hace el agente, con sus argumentos y resultados. Por ejemplo:

```
[API] Mensaje recibido: da de alta una RTX 4090 a 1200 euros
[RPA] Ejecutando workflow: alta_hardware_v1.workflow.json con params: {'nombre': 'RTX 4090', ...}
[SERVIDOR] Producto guardado: RTX 4090
```

Esto evidencia que el agente razona y orquesta las tools el solo, sin pipelines cableados.

## Estructura del proyecto

```
rpa/
  requirements.txt     -> dependencias Python
  RPA_Agent_API/       -> backend (FastAPI + agente LangGraph)
    agent/
      agent.py         -> construccion del agente y bucle de chat CLI
      tools.py         -> las 4 herramientas del agente
      runner.py        -> motor RPA con Playwright
    rag/
      index_procedures.py  -> indexa los workflows en ChromaDB
    shared/
      templating.py    -> sustituye placeholders en los workflows
    procedures/        -> workflows JSON grabados con el recorder
    web_form/
      index.html       -> formulario + recorder JS integrado
      server.py        -> servidor local del formulario
    api.py             -> API FastAPI que expone el agente
  RPA_Agent_UI/        -> interfaz MAUI Blazor
```

## Como arrancarlo

Requisito previo: tener LM Studio abierto con el servidor local en el puerto 1234.

**1. Levantar el formulario web:**
```
cd RPA_Agent_API/web_form
python server.py
```

**2. Indexar los workflows en ChromaDB (solo la primera vez):**
```
cd RPA_Agent_API
python rag/index_procedures.py
```

**3. Levantar la API del agente:**
```
cd RPA_Agent_API
uvicorn api:app --reload --port 8000
```

**4. Abrir RPA_Agent_UI en Visual Studio y ejecutar.**

Para instalar las dependencias Python la primera vez:
```
pip install -r requirements.txt
playwright install chromium
```
