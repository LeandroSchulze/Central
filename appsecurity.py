# app/security.py
from datetime import datetime

def registrar_evento(mensaje: str):
    # Esto imprimirá de forma limpia en la consola de Railway para tus auditorías
    print(f"[{datetime.utcnow().isoformat()}] [EVENTO_PANEL] {mensaje}")
