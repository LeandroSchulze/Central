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
# 🛡️ CARGA DIRECTA DEL DASHBOARD
# =====================================================================
def obtener_ruta_dashboard() -> str:
    # Busca dashboard.html en la raíz o en la carpeta templates
    base = os.getcwd()
    if os.path.exists(os.path.join(base, "dashboard.html")):
        return os.path.join(base, "dashboard.html")
    return os.path.join(base, "templates", "dashboard.html")

@app.get("/", response_class=HTMLResponse)
def index(): 
    # Carga directa sin pasar por login
    return FileResponse(obtener_ruta_dashboard())

app.include_router(router)
