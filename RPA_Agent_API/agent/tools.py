
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

# 1. Herramienta para buscar el procedimiento correcto
@tool
def search_procedures(query: str) -> str:
    """
    Util para buscar que procedimiento o workflow se debe ejecutar en base a la peticion del usuario.
    Recibe la intencion del usuario y devuelve el ID del procedimiento y los parametros que necesita.
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
        return "No se encontraron procedimientos que coincidan con la peticion."
        
    doc, score = resultados[0]
    metadata = doc.metadata
    
    return f"Procedimiento encontrado: ID={metadata['filename']}, Schema={metadata['param_schema']}"

# 2. Herramienta para extraer los parametros usando el LLM
@tool
def extract_parameters(peticion_original: str, param_schema: str) -> dict:
    """
    Recibe la peticion del usuario y el param_schema. Extrae los datos de la peticion y los devuelve
    como un diccionario JSON valido con las claves del schema (ej: nombre, precio, stock, categoria).
    """
    llm = ChatOpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio", temperature=0)
    
    prompt = PromptTemplate.from_template(
        "Extrae los parametros de la siguiente peticion basandote en este esquema: {schema}\n"
        "Peticion: {peticion}\n"
        "Devuelve UNICAMENTE un JSON valido, sin formato markdown ni texto adicional."
    )
    
    cadena = prompt | llm
    respuesta = cadena.invoke({"schema": param_schema, "peticion": peticion_original})
    
    texto_json = respuesta.content.replace("```json", "").replace("```", "").strip()
    
    try:
        return json.loads(texto_json)
    except json.JSONDecodeError:
        return {"error": "Fallo al extraer parametros. Pide al usuario que aclare los datos."}

# 3. Herramienta para ejecutar el RPA (con Human-in-the-Loop)
@tool
def run_workflow(workflow_id: str, params: dict) -> str:
    """
    Ejecuta la automatizacion web (RPA) pasandole el ID del procedimiento y el diccionario de parametros.
    IMPORTANTE: Antes de ejecutar, SIEMPRE pide confirmacion al usuario mostrando los parametros extraidos.
    Solo ejecuta si el usuario responde afirmativamente.
    """
    # --- HUMAN IN THE LOOP ---
    # Se pausa el agente y se le piden los datos al usuario para que confirme.
    params_legibles = "\n".join([f"  - {k}: {v}" for k, v in params.items()])
    confirmacion = interrupt(
        f"📋 Voy a ejecutar el RPA con estos datos:\n{params_legibles}\n\n"
        f"¿Confirmas el registro? (responde 'si' o 'no')"
    )
    # --- FIN HUMAN IN THE LOOP ---

    if confirmacion.strip().lower() not in ["si", "sí", "yes", "s", "ok", "confirmar"]:
        return "❌ Operacion cancelada por el usuario."

    print(f"\n[Ejecutando RPA] Workflow: {workflow_id} | Params: {params}")
    resultado = run_workflow_playwright(workflow_id, params)

    if resultado["status"] == "ok":
        return f"✅ Exito. Duracion: {resultado['duration']}s. Mensaje capturado: {resultado['last_toast']}"
    else:
        return f"❌ Error en la automatizacion: {resultado['message']}"

# 4. Herramienta para listar todos los procedimientos
@tool
def list_procedures(query: str = "") -> str:
    """
    Devuelve una lista con todos los procedimientos disponibles en el sistema.
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