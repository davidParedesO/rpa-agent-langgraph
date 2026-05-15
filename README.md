# Practica RPA + RAG con LangGraph

Proyecto de la practica de RPA para la asignatura. Consiste en un agente inteligente que puede registrar equipamiento IT en un formulario web de forma automatica a partir de una peticion en lenguaje natural.

## Como funciona

El usuario escribe algo como "da de alta un monitor a 150 euros" y el agente:
1. Busca en ChromaDB el workflow correcto (search_procedures)
2. Extrae los parametros de la frase (extract_parameters)
3. Pide confirmacion antes de ejecutar
4. Si el usuario confirma, Playwright rellena el formulario automaticamente (run_workflow)

## Estructura del proyecto

```
rpa/
  RPA_Agent_API/       -> backend Python (FastAPI + agente LangGraph)
    agent/
      agent.py         -> construccion del agente y bucle de chat
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

## Por que LangGraph y no LangChain clasico

Use LangGraph porque permite mantener el estado de la conversacion entre turnos con MemorySaver,
lo que hace posible un chat real multi-turno. Ademas, tiene soporte para interrupciones (interrupt)
que me permitio implementar la confirmacion antes de ejecutar el RPA sin tener que cablear nada a mano.
Con LangChain clasico esto seria bastante mas complicado de hacer.

## Como arrancarlo

**1. Levantar el formulario web:**
```
cd RPA_Agent_API/web_form
python server.py
```

**2. Indexar los workflows (solo la primera vez):**
```
cd RPA_Agent_API
python rag/index_procedures.py
```

**3. Levantar la API:**
```
cd RPA_Agent_API
uvicorn api:app --reload --port 8000
```

**4. Abrir RPA_Agent_UI en Visual Studio y ejecutar.**

LM Studio tiene que estar corriendo con el servidor local en el puerto 1234.
