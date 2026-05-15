import json

def render_placeholders(workflow_steps: list, params: dict) -> list:
    """
    Sustituye los placeholders {{clave}} en los steps del workflow
    por los valores reales pasados en el diccionario params.
    """
    # Convertimos la lista de pasos a texto para hacer un replace masivo
    steps_str = json.dumps(workflow_steps)
    
    for key, value in params.items():
        # Busca el patrón {{key}} y lo reemplaza
        steps_str = steps_str.replace(f"{{{{{key}}}}}", str(value))
        
    # Volvemos a convertir el texto a lista de diccionarios Python
    return json.loads(steps_str)