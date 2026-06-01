import os
import sys
from datetime import datetime
from fastapi import FastAPI, APIRouter, Header, HTTPException
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

# --- Escudo de Rutas para Railway ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

load_dotenv()

app = FastAPI(
    title="Torre de Control",
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
# 🛡️ CARGA ULTRA-SEGURA DEL DASHBOARD (SIN ERROR 500)
# =====================================================================
def leer_dashboard_html() -> str:
    # Escanea todas las carpetas del proyecto buscando tu dashboard.html
    directorios_a_escanear = ["/app", os.getcwd()]
    
    for base in directorios_a_escanear:
        if os.path.exists(base):
            for root, dirs, files in os.walk(base):
                if "dashboard.html" in files:
                    ruta_exacta = os.path.join(root, "dashboard.html")
                    try:
                        with open(ruta_exacta, "r", encoding="utf-8") as f:
                            return f.read()
                    except Exception as e:
                        return f"<h1>Error al leer el archivo HTML: {e}</h1>"
    
    # Si el archivo NO se subió a GitHub, mostramos esto en lugar de crashear:
    return '''
    <div style="font-family: sans-serif; padding: 40px; text-align: center; background: #111827; color: white; height: 100vh;">
        <h2 style="color: #ef4444;">¡Falta el archivo dashboard.html!</h2>
        <p>El servidor de Python y tu API arrancaron perfecto, pero falta el HTML.</p>
        <p>Asegurate de haber commiteado el archivo <b>dashboard.html</b> a tu repo de GitHub.</p>
    </div>
    '''

@app.get("/", response_class=HTMLResponse)
def index(): 
    # Devolvemos el HTML procesado directamente, erradicando el FileResponse
    return HTMLResponse(content=leer_dashboard_html(), status_code=200)

app.include_router(router)

# =====================================================================
# 🔌 CONEXIÓN DE MÓDULOS DE MÉTRICAS E IA
# =====================================================================
try:
    from metrics import router as metrics_router
    app.include_router(metrics_router)
    print("[OK] Módulo de Métricas conectado.")
except Exception as e:
    print(f"[ERROR] No se pudo cargar metrics.py: {e}")

try:
    from ai_advisor import router as ai_router
    app.include_router(ai_router)
    print("[OK] Módulo de IA conectado.")
except Exception as e:
    print(f"[ERROR] No se pudo cargar ai_advisor.py: {e}")
