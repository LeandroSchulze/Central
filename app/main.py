import os
from datetime import datetime
from fastapi import FastAPI, APIRouter, Header, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Torre de Control - Acceso Directo",
    description="Panel unificado de monitoreo sin autenticación (Acceso privado vía Railway)",
    version="1.0.0"
)

router = APIRouter()

# ==========================================
# CÓDIGO DE CONTROL DE TIPO DE CAMBIO
# ==========================================
TOKEN_INTERNO_SECRETO = os.getenv("TOKEN_SISTEMAS_SECRETO")
raw_cotizacion = os.getenv("COTIZACION", "1000.0").strip()
try:
    TIPO_CAMBIO = float(raw_cotizacion)
except ValueError:
    TIPO_CAMBIO = 1000.0

@router.post("/api/v1/internal/update-tc")
def actualizar_tipo_cambio_interno(payload: dict, x_internal_token: str = Header(None)):
    global TIPO_CAMBIO
    if x_internal_token != TOKEN_INTERNO_SECRETO or not TOKEN_INTERNO_SECRETO:
        raise HTTPException(status_code=401, detail="No autorizado")
    
    nuevo_tc = payload.get("nuevo_tc")
    if nuevo_tc is None or not isinstance(nuevo_tc, (int, float)):
        raise HTTPException(status_code=400, detail="Valor de TC inválido")
    
    TIPO_CAMBIO = float(nuevo_tc)
    return {"status": "actualizado", "nuevo_tipo_cambio": TIPO_CAMBIO}

# =====================================================================
# 🛡️ CARGA DIRECTA DEL DASHBOARD DESDE LA CARPETA STATIC
# =====================================================================
def obtener_ruta_dashboard() -> str:
    # Busca dashboard.html específicamente dentro de la carpeta 'static'
    base = os.getcwd()
    
    # Intenta buscar en app/static/dashboard.html (si Railway ejecuta desde /app)
    ruta_app_static = os.path.join(base, "app", "static", "dashboard.html")
    if os.path.exists(ruta_app_static):
        return ruta_app_static
        
    # Intenta buscar en static/dashboard.html (si Railway ejecuta desde la raíz del repo)
    ruta_static = os.path.join(base, "static", "dashboard.html")
    if os.path.exists(ruta_static):
        return ruta_static
        
    # Fallback relativo
    return os.path.join("static", "dashboard.html")

@app.get("/", response_class=HTMLResponse)
def index(): 
    # Carga directa sin pasar por login, buscando en 'static'
    ruta = obtener_ruta_dashboard()
    if os.path.exists(ruta):
        return FileResponse(ruta)
    
    # Pantalla de emergencia si sigue sin encontrarlo
    html_emergencia = f"""
    <html>
        <body style='background:#1f2937; color:#f9fafb; font-family:sans-serif; text-align:center; padding:10%;'>
            <h1 style='color:#60a5fa;'>Torre de Control Activa 🚀</h1>
            <p>El servidor Python está funcionando, pero el archivo HTML no se encuentra en la ruta esperada.</p>
            <div style='background:#374151; padding:20px; border-radius:10px; display:inline-block; margin-top:20px;'>
                <p style='color:#f87171;'>⚠️ No se encontró <b>dashboard.html</b> dentro de la carpeta <b>static</b>.</p>
                <p style='font-size:14px; color:#9ca3af;'>Ruta buscada: {ruta}</p>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_emergencia, status_code=200)

app.include_router(router)
