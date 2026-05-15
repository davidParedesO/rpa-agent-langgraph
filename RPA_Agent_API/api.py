from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from agent.tools import search_procedures, extract_parameters, run_workflow, list_procedures

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "sesion_david_03"


class ResumeRequest(BaseModel):
    confirmation: str
    thread_id: str = "sesion_david_03"


llm = ChatOpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio",
    model="google/gemma-2-9b",
    temperature=0
)

tools = [search_procedures, extract_parameters, run_workflow, list_procedures]
memory = MemorySaver()

system_prompt = """Eres un asistente que ayuda a registrar equipamiento IT. 
REGLA CRÍTICA: Cuando pases la categoría a la herramienta run_workflow, usa EXACTAMENTE uno de estos nombres (con sus paréntesis y tildes):
- "Portátiles / Laptops"
- "Componentes PC (CPU, GPU, RAM)"
- "Periféricos (Monitores, Teclados)"
- "Equipos de Red (Routers, Switches)"

Pasos:
1. Busca el workflow.
2. Extrae datos.
3. Pide confirmación al usuario.
4. Ejecuta run_workflow solo si el usuario dice 'si'.
Responde siempre en español."""

agent = create_react_agent(
    model=llm,
    tools=tools,
    checkpointer=memory,
    prompt=system_prompt
)


def ejecutar_agente(input_data, config) -> dict:
    respuesta = "No pude procesar la solicitud."
    for event in agent.stream(input_data, config=config, stream_mode="values"):
        # si el agente se pausa esperando confirmacion del usuario
        if "__interrupt__" in event:
            info = event["__interrupt__"]
            mensaje = info[0].value if info else "Confirmas la operacion?"
            return {"reply": mensaje, "awaiting_confirmation": True}
        mensajes = event.get("messages", [])
        if mensajes:
            ultimo = mensajes[-1]
            if hasattr(ultimo, "content") and ultimo.content and ultimo.type == "ai":
                respuesta = ultimo.content
    return {"reply": respuesta, "awaiting_confirmation": False}


@app.post("/chat")
async def chat(request: ChatRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    print(f"[API] Mensaje recibido: {request.message}")
    try:
        resultado = ejecutar_agente({"messages": [HumanMessage(content=request.message)]}, config)
        return resultado
    except Exception as e:
        print(f"[API] Error: {e}")
        return {"reply": "Error en el agente, revisa la consola.", "awaiting_confirmation": False}

@app.post("/resume")
async def resume_endpoint(request: ResumeRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    print(f"\n[API] Reanudando agente con: '{request.confirmation}'")
    try:
        resultado = ejecutar_agente(Command(resume=request.confirmation), config)
        print(f"[API] Respuesta tras reanudar: {resultado}")
        return resultado
    except Exception as e:
        print(f"[API] Error al reanudar: {e}")
        return {"reply": "Error al reanudar el agente.", "awaiting_confirmation": False}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)