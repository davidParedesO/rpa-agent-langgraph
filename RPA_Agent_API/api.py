# -*- coding: utf-8 -*-
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
    thread_id: str = "usuario_david_01"

class ResumeRequest(BaseModel):
    confirmation: str
    thread_id: str = "usuario_david_01"

llm = ChatOpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio",
    model="google/gemma-2-9b",
    temperature=0
)

tools = [search_procedures, extract_parameters, run_workflow, list_procedures]
memory = MemorySaver()

system_instructions = """Eres un asistente RPA autonomo. Tu objetivo es ayudar al usuario a registrar hardware.
Reglas:
1. Si el usuario pide registrar un producto, usa search_procedures para buscar el workflow.
2. Luego usa extract_parameters para sacar los datos.
3. Finalmente usa run_workflow para ejecutar el RPA (pedira confirmacion al usuario automaticamente).
4. Si faltan datos obligatorios, pregunta al usuario. No inventes datos.
5. Las categorias validas son: componentes, perifericos, portatiles, redes.
Responde siempre en espanol."""

agent = create_react_agent(
    model=llm,
    tools=tools,
    checkpointer=memory,
    prompt=system_instructions
)


def _run_agent_stream(input_data, config) -> dict:
    respuesta_final = "No he podido procesar tu solicitud."
    for event in agent.stream(input_data, config=config, stream_mode="values"):
        if "__interrupt__" in event:
            interrupt_info = event["__interrupt__"]
            mensaje = interrupt_info[0].value if interrupt_info else "Confirmas la operacion?"
            return {"reply": mensaje, "awaiting_confirmation": True}
        messages = event.get("messages", [])
        if messages:
            ultimo = messages[-1]
            if hasattr(ultimo, "content") and ultimo.content and ultimo.type == "ai":
                respuesta_final = ultimo.content
    return {"reply": respuesta_final, "awaiting_confirmation": False}


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    print(f"\n[API] MAUI dice: {request.message}")
    try:
        resultado = _run_agent_stream(
            {"messages": [HumanMessage(content=request.message)]},
            config
        )
        print(f"[API] Respondiendo: {resultado}")
        return resultado
    except Exception as e:
        print(f"[API] Error: {e}")
        return {"reply": "Error interno del Agente. Revisa la consola.", "awaiting_confirmation": False}


@app.post("/resume")
async def resume_endpoint(request: ResumeRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    print(f"\n[API] Reanudando agente con: '{request.confirmation}'")
    try:
        resultado = _run_agent_stream(Command(resume=request.confirmation), config)
        print(f"[API] Respuesta tras reanudar: {resultado}")
        return resultado
    except Exception as e:
        print(f"[API] Error al reanudar: {e}")
        return {"reply": "Error al reanudar el agente.", "awaiting_confirmation": False}
