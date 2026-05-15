import json
import os
import time
from playwright.sync_api import sync_playwright
# Importamos la funcion que acabamos de crear
from shared.templating import render_placeholders

def run_workflow_playwright(workflow_filename: str, params: dict):
    # 1. Buscar el JSON en la carpeta procedures
    workflow_path = os.path.join("procedures", workflow_filename)
    
    if not os.path.exists(workflow_path):
        return {"status": "error", "message": f"No se encontro el workflow: {workflow_filename}"}
        
    with open(workflow_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)
        
    # 2. Inyectar los datos reales
    steps = render_placeholders(workflow["steps"], params)
    url = workflow["url"]
    
    result = {"status": "ok", "duration": 0, "last_toast": ""}
    start_time = time.time()
    
    # 3. Arrancar Playwright y ejecutar pasos
    print(f"\n[RPA] Iniciando automatizacion en: {url}")
    with sync_playwright() as p:
        # headless=False para que veas como se mueve solo.
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        page = browser.new_page()
        page.goto(url)
        
        for step in steps:
            step_type = step.get("type")
            
            if step_type == "wait":
                page.wait_for_timeout(step["ms"])
                
            elif step_type in ["click", "type", "select", "wait_for_text"]:
                target = step["target"]
                # Formateamos el selector CSS (por id o por name)
                selector = f"#{target['value']}" if target['by'] == "id" else f"[name='{target['value']}']"
                
                try:
                    if step_type == "click":
                        page.click(selector)
                    elif step_type == "type":
                        page.fill(selector, step["value"])
                    elif step_type == "select":
                        page.select_option(selector, step["value"])
                    elif step_type == "wait_for_text":
                        # Espera a que el toast verde aparezca
                        page.locator(selector).filter(has_text=step["contains"]).wait_for(state="visible", timeout=5000)
                        result["last_toast"] = page.locator(selector).inner_text()
                except Exception as e:
                    browser.close()
                    return {"status": "error", "message": f"Fallo en step {step_type} sobre {selector}: {str(e)}"}

        browser.close()
        
    result["duration"] = round(time.time() - start_time, 2)
    return result

# --- ZONA DE PRUEBAS ---
if __name__ == "__main__":
    datos_prueba = {
        "nombre": "Monitor UltraWide 34",
        "precio": "450.50",
        "stock": "12",
        "categoria": "perifericos"
    }
    
    print("Iniciando prueba del motor RPA...")
    resultado = run_workflow_playwright("alta_hardware_v1.workflow.json", datos_prueba)
    print("\nResultado final:", resultado)