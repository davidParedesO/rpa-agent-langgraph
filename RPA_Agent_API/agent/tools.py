import os
import json
from langchain_core.tools import tool
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langgraph.types import interrupt
from agent.runner import run_workflow_playwright

CHROMA_DB_DIR = "chroma_db"
PROCEDURES_DIR = "procedures"


@tool
def search_procedures(query: str) -> str:
    """
    Busca en la base de datos vectorial el workflow mas adecuado segun la peticion del usuario.
    Devuelve el ID del procedimiento y el esquema de parametros que necesita para ejecutarse.
    Usala cuando el usuario quiera realizar alguna accion y necesites saber que workflow usar.
    """
    embeddings = OpenAIEmbeddings(
        base_url="http://localhost:1234/v1",
        api_key="lm-studio",
        model="text-embedding-nomic-embed-text-v1.5",
        check_embedding_ctx_length=False
    )

    vectorstore = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
    resultados = vectorstore.similarity_search_with_score(query, k=1)

    if not resultados:
        return "No se encontro ningun procedimiento que coincida con la peticion."

    doc, score = resultados[0]
    metadata = doc.metadata

    return f"Procedimiento encontrado: ID={metadata['filename']}, Schema={metadata['param_schema']}"


@tool
def extract_parameters(peticion_original: str, param_schema: str) -> dict:
    """
    Extrae los parametros necesarios de la peticion del usuario segun el esquema indicado.
    Devuelve un diccionario con los valores listos para ejecutar el workflow.
    Usala despues de encontrar el workflow con search_procedures.
    """
    llm = ChatOpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio", temperature=0)

    prompt = PromptTemplate.from_template(
        "Extrae los parametros de la siguiente peticion segun este esquema: {schema}\n"
        "Peticion: {peticion}\n"
        "Devuelve solo un JSON valido, sin texto adicional ni bloques de codigo."
    )

    cadena = prompt | llm
    respuesta = cadena.invoke({"schema": param_schema, "peticion": peticion_original})

    # a veces el modelo devuelve el json dentro de ```json ... ``` asi que lo limpiamos
    texto_json = respuesta.content.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(texto_json)
    except json.JSONDecodeError:
        return {"error": "No se pudieron extraer los parametros. Pide al usuario que aclare los datos."}


@tool
def run_workflow(workflow_id: str, params: dict) -> str:
    """
    Ejecuta el RPA con el workflow indicado y los parametros extraidos.
    Antes de ejecutar pide confirmacion al usuario mostrando los datos que va a usar.
    Solo ejecuta si el usuario confirma. Si dice que no, cancela la operacion.
    """
    # mostramos los datos al usuario y esperamos confirmacion antes de lanzar playwright
    params_texto = "\n".join([f"  {k}: {v}" for k, v in params.items()])
    confirmacion = interrupt(
        f"Voy a registrar el equipo con estos datos:\n{params_texto}\n\nConfirmas? (si / no)"
    )

    if confirmacion.strip().lower() not in ["si", "sí", "yes", "s", "ok", "confirmar"]:
        return "Operacion cancelada."

    print(f"[RPA] Ejecutando workflow: {workflow_id} con params: {params}")
    resultado = run_workflow_playwright(workflow_id, params)

    if resultado["status"] == "ok":
        return f"Hecho. Tardo {resultado['duration']}s. El formulario mostro: {resultado['last_toast']}"
    else:
        return f"Error al ejecutar el RPA: {resultado['message']}"


@tool
def list_procedures(query: str = "") -> str:
    """
    Devuelve la lista de todos los workflows disponibles en el sistema.
    Usala cuando no tengas claro que procedimiento usar o la peticion sea ambigua.
    """
    procedimientos = []
    if os.path.exists(PROCEDURES_DIR):
        for filename in os.listdir(PROCEDURES_DIR):
            if filename.endswith(".json"):
                with open(os.path.join(PROCEDURES_DIR, filename), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    procedimientos.append(f"- {data['id']} ({filename}): {data['titulo']}")

    if procedimientos:
        return "\n".join(procedimientos)
    return "No hay procedimientos registrados."
