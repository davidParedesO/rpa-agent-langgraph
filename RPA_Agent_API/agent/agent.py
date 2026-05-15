from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from agent.tools import search_procedures, extract_parameters, run_workflow, list_procedures


def main():
    llm = ChatOpenAI(
        base_url="http://localhost:1234/v1",
        api_key="lm-studio",
        model="qwen/qwen3-coder-30b",
        temperature=0
    )

    tools = [search_procedures, extract_parameters, run_workflow, list_procedures]
    memory = MemorySaver()

    system_prompt = """Eres un asistente que ayuda a registrar equipamiento IT en el sistema.
Cuando el usuario quiera dar de alta un dispositivo, busca primero el workflow con search_procedures,
luego extrae los datos con extract_parameters y finalmente ejecuta el RPA con run_workflow.
Si te faltan datos como el nombre, precio, stock o categoria, pregunta antes de continuar.
Si la peticion no esta clara, usa list_procedures para ver que opciones hay.
Responde siempre en espanol y de forma concisa."""

    agent = create_react_agent(
        model=llm,
        tools=tools,
        checkpointer=memory,
        prompt=system_prompt
    )

    thread_id = "sesion_rpa_01"
    config = {"configurable": {"thread_id": thread_id}}

    print("\n" + "="*40)
    print("Agente RPA iniciado. Escribe 'salir' para terminar.")
    print("="*40 + "\n")

    while True:
        user_input = input("Tu: ")
        if user_input.lower() in ["salir", "exit", "quit"]:
            break

        mensaje = HumanMessage(content=user_input)
        print("\n[pensando...]\n")
        try:
            for event in agent.stream({"messages": [mensaje]}, config=config):
                for key, value in event.items():
                    if "messages" in value:
                        for msg in value["messages"]:
                            if msg.type == "ai" and msg.content:
                                print(f"Agente: {msg.content}")
        except Exception as e:
            print(f"Error: {e}")
            print("Comprueba que LM Studio este corriendo.")


if __name__ == "__main__":
    main()
