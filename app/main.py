from fastapi import FastAPI, HTTPException, status, Request, APIRouter, Header
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, EmailStr
import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

from auth import AuthManager
from security import registrar_evento

load_dotenv()

app = FastAPI(
    title="Panel Central - AlertTrail & ComplianceFlow",
    description="Panel unificado para monitoreo de usuarios, pagos, métricas y control del tipo de cambio.",
    version="1.0.0"
)

auth_handler = AuthManager()
router = APIRouter()

# ==========================================
# CÓDIGO DE CONTROL DE TIPO DE CAMBIO
# ==========================================
TOKEN_INTERNO_SECRETO = os.getenv("TOKEN_SISTEMAS_SECRETO")

# Convertimos la cotización base de forma segura
raw_cotizacion = os.getenv("COTIZACION", "1000.0").strip()
try:
    TIPO_CAMBIO = float(raw_cotizacion)
except ValueError:
    TIPO_CAMBIO = 1000.0

@router.post("/api/v1/internal/update-tc")
def actualizar_tipo_cambio_interno(payload: dict, x_internal_token: str = Header(None)):
    global TIPO_CAMBIO
    
    # Validamos que la petición venga realmente de tus plataformas autorizadas
    if x_internal_token != TOKEN_INTERNO_SECRETO or not TOKEN_INTERNO_SECRETO:
        raise HTTPException(status_code=401, detail="No autorizado")
    
    nuevo_tc = payload.get("nuevo_tc")
    if nuevo_tc is None or not isinstance(nuevo_tc, (int, float)):
        raise HTTPException(status_code=400, detail="Valor de TC inválido")
    
    # Se actualiza en la memoria del servidor
    TIPO_CAMBIO = float(nuevo_tc)
    registrar_evento(f"Tipo de cambio actualizado mediante IA/Panel a: {TIPO_CAMBIO}")
    return {"status": "actualizado", "nuevo_tipo_cambio": TIPO_CAMBIO}


# --- MODELOS DE DATOS (PYDANTIC) ---
class UserRegister(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    codigo_mfa: str


# --- CONEXIÓN A BASE DE DATOS POSTGRES ---
def obtener_conexion_db():
    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(db_url)


# =====================================================================
# 📊 ENDPOINTS DE MÉTRICAS (ALERTTRAIL & COMPLIANCEFLOW)
# =====================================================================
@app.get("/api/metrics/summary", tags=["Métricas Centrales"])
def obtener_resumen_panel():
    """
    Endpoint principal del Dashboard para leer el estado de tus otras dos apps.
    Aquí harás las consultas SQL a tu base de datos compartida o vinculada.
    """
    try:
        with obtener_conexion_db() as conn:
            with conn.cursor() as cursor:
                return {
                    "tipo_cambio_actual": TIPO_CAMBIO,
                    "usuarios": {
                        "nuevos_hoy": 0,       
                        "activos_totales": 0   
                    },
                    "financiero": {
                        "pagos_procesados_mes": 0,
                        "moneda": "ARS"
                    },
                    "alerttrail": {
                        "alertas_emitidas_hoy": 0,
                        "logs_escaneados_total": 0
                    },
                    "complianceflow": {
                        "usuarios_premium_activos": 0
                    },
                    "actualizado_en": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al conectar con la base de datos de métricas: {str(e)}")


# =====================================================================
# 🛡️ RESOLVEDOR INTELIGENTE DE RUTAS PARA HTML
# =====================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def obtener_ruta_template(nombre_archivo: str) -> str:
    # Opción 1: En la raíz del repositorio (/app/templates/)
    ruta_raiz = os.path.join(os.path.dirname(BASE_DIR), "templates", nombre_archivo)
    if os.path.exists(ruta_raiz):
        return ruta_raiz
    # Opción 2: Dentro de la subcarpeta app (/app/app/templates/)
    ruta_interna = os.path.join(BASE_DIR, "templates", nombre_archivo)
    if os.path.exists(ruta_interna):
        return ruta_interna
    # Fallback relativo por defecto
    return os.path.join("templates", nombre_archivo)


# --- VISTAS HTML REPARADAS ---
@app.get("/", response_class=HTMLResponse)
def index(): 
    return FileResponse(obtener_ruta_template("index.html"))

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(): 
    return FileResponse(obtener_ruta_template("dashboard.html"))

@app.get("/login", response_class=HTMLResponse)
def mostrar_login(): 
    return FileResponse(obtener_ruta_template("login.html"))


# --- AUTENTICACIÓN ---
@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED, tags=["Autenticación"])
def registrar(usuario: UserRegister):
    try:
        mfa_secret = auth_handler.registrar_usuario(usuario.email, usuario.password)
        return {"mensaje": "Usuario registrado exitosamente", "mfa_secret": mfa_secret}
    except Exception as e: 
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login", tags=["Autenticación"])
def login(usuario: UserLogin):
    codigo_limpio = usuario.codigo_mfa.replace(" ", "").replace("-", "").strip()
    if not auth_handler.verificar_mfa(usuario.email, codigo_limpio):
        raise HTTPException(status_code=401, detail="MFA inválido.")
    return {"mensaje": "Acceso concedido"}


# REGISTRO DEL ROUTER
app.include_router(router)
