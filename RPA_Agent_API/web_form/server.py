import http.server
import socketserver
import os
import json
import urllib.parse
from datetime import datetime

PORT = 8081
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(DIRECTORY, "inventario.json")


def cargar_inventario():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def guardar_inventario(datos):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_POST(self):
        if self.path == "/guardar":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            campos = urllib.parse.parse_qs(body)

            producto = {
                "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                "nombre": campos.get("nombre", [""])[0],
                "precio": campos.get("precio", [""])[0],
                "stock": campos.get("stock", [""])[0],
                "categoria": campos.get("categoria", [""])[0],
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            inventario = cargar_inventario()
            inventario.append(producto)
            guardar_inventario(inventario)

            print(f"[SERVIDOR] Producto guardado: {producto['nombre']}")

            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # silencia los logs de peticiones GET para no ensuciar la consola


with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Servidor sirviendo el formulario en: http://localhost:{PORT}")
    print(f"Los productos se guardan en: {DB_FILE}")
    httpd.serve_forever()
