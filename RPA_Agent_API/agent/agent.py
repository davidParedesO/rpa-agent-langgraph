from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from agent.tools import search_procedures, extract_parameters, run_workflow, list_procedures

def main():
    # 1. Configurar la conexion a tu LM Studio local
    llm = ChatOpenAI(
        base_url="http://localhost:1234/v1",
        api_key="lm-studio",
        model="qwen/qwen3-coder-30b", # Tu modelo de Llama 3
        temperature=0
    )

    # 2. Cargar las herramientas que acabamos de crear
    tools = [search_procedures, extract_parameters, run_workflow, list_procedures]

    # 3. Configurar la memoria (Obligatorio en LangGraph para que haya chat real)
    memory = MemorySaver()

    # 4. Las instrucciones del cerebro del Agente
    system_prompt = """Eres un asistente RPA autonomo. Tu objetivo es ayudar al usuario a registrar hardware en un sistema.
    Reglas:
    1. Si el usuario te pide registrar un producto, usa 'search_procedures' para buscar el workflow.
    2. Luego, usa 'extract_parameters' para sacar los datos de su frase.
    3. Finalmente, usa 'run_workflow' con el ID y los parametros para ejecutar el RPA.
    4. Si te faltan datos obligatorios (nombre, precio, stock, categoria), PREGUNTA al usuario en lugar de inventarlos.
    Responde siempre de forma breve y en espanol."""

    # 5. Crear el grafo del Agente ReAct
    agent = create_react_agent(
        model=llm,
        tools=tools,
        checkpointer=memory,
        prompt=system_prompt
    )

    # 6. Bucle de chat en la terminal
    thread_id = "sesion_rpa_01"
    config = {"configurable": {"thread_id": thread_id}}

    print("\n" + "="*50)
    print(" AGENTE ORQUESTADOR RPA INICIADO")
    print("Escribe 'salir' para terminar el chat.")
    print("="*50 + "\n")

    while True:
        user_input = input("Tu: ")
        if user_input.lower() in ['salir', 'exit', 'quit']:
            break
            
        mensaje = HumanMessage(content=user_input)
        
        print("\n[Agente pensando y usando herramientas...]")
        try:
            # agent.stream nos permite ver los pasos que va dando
            for event in agent.stream({"messages": [mensaje]}, config=config):
                for key, value in event.items():
                    if "messages" in value:
                        for msg in value["messages"]:
                            if msg.type == "ai" and msg.content:
                                print(f" Agente: {msg.content}")
        except Exception as e:
            print(f"Error en la ejecucion: {e}")
            print("Asegurate de que LM Studio esta encendido y el servidor local iniciado.")

if __name__ == "__main__":
    main()