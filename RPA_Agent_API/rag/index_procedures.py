import os
import json
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings # <--- Importamos la de OpenAI

PROCEDURES_DIR = "procedures"
CHROMA_DB_DIR = "chroma_db"

def index_workflows():
    print("Iniciando indexacion de procedimientos...")
    
    documents = []
    for filename in os.listdir(PROCEDURES_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(PROCEDURES_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                workflow = json.load(f)
                
                content = f"Titulo: {workflow['titulo']}\nDescripcion: {workflow['descripcion']}\nTags: {', '.join(workflow['tags'])}"
                metadata = {
                    "id": workflow["id"],
                    "filename": filename,
                    "param_schema": json.dumps(workflow["param_schema"])
                }
                
                doc = Document(page_content=content, metadata=metadata)
                documents.append(doc)
                print(f" -> Cargado para indexar: {workflow['titulo']}")

    if not documents:
        print("No se encontraron workflows en la carpeta procedures/")
        return

    # --- AQUI ESTA EL CAMBIO ---
    # Nos conectamos a tu LM Studio local para los Embeddings
    print("\nConectando con LM Studio para generar vectores...")
    embeddings = OpenAIEmbeddings(
        base_url="http://localhost:1234/v1",
        api_key="lm-studio",
        model="text-embedding-nomic-embed-text-v1.5",
       check_embedding_ctx_length=False 
    )

    print(f"\nGuardando {len(documents)} procedimientos en ChromaDB ({CHROMA_DB_DIR})...")
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=CHROMA_DB_DIR
    )
    
    print("\n[OK] Indexacion RAG completada con exito usando LM Studio.")

if __name__ == "__main__":
    index_workflows()