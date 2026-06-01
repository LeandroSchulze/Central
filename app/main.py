import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Torre de Control",
    description="Panel unificado para monitoreo de métricas, pagos y seguridad.",
    version="1.0.0"
)

# =====================================================================
# 🛡️ BUSCADOR RECURSIVO DEL DASHBOARD (Evita el Error 500)
# =====================================================================
def obtener_ruta_dashboard() -> str:
    # Escanea todo el contenedor buscando el archivo, esté donde esté
    directorios_base = ["/app", os.getcwd()]
    
    for base in directorios_base:
        if os.path.exists(base):
            for root, dirs, files in os.walk(base):
                if "dashboard.html" in files:
                    return os.path.join(root, "dashboard.html")
                    
    return "dashboard.html"

# --- VISTA PRINCIPAL ---
@app.get("/", response_class=HTMLResponse)
def index(): 
    ruta = obtener_ruta_dashboard()
    
    if os.path.exists(ruta):
        return FileResponse(ruta)
        
    # Si el archivo no existe en el repo, mostramos una web de emergencia
    html_emergencia = """
    <html>
        <body style='background:#1f2937; color:#f9fafb; font-family:sans-serif; text-align:center; padding:10%;'>
            <h1 style='color:#60a5fa;'>Torre de Control Activa 🚀</h1>
            <p>El servidor Python está funcionando perfecto.</p>
            <div style='background:#374151; padding:20px; border-radius:10px; display:inline-block; margin-top:20px;'>
                <p style='color:#f87171;'>⚠️ No se encontró el archivo <b>dashboard.html</b></p>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_emergencia, status_code=200)
