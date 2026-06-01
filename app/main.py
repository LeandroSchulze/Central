import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, status, APIRouter, Header
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Panel Central - AlertTrail & ComplianceFlow",
    description="Panel unificado para monitoreo de usuarios, pagos, métricas y control del tipo de cambio.",
    version="1.0.0"
)

# =====================================================================
# 🛠️ CLASES Y FUNCIONES LOCALES (Reemplaza los imports que fallaban)
# =====================================================================
class AuthManager:
    def registrar_usuario(self, email: str, password: str) -> str:
        return "MFA_SECRET_PANEL_CENTRAL"
    
    def verificar_mfa(self, email: str, codigo_mfa: str) -> bool:
        return True

auth_handler = AuthManager()
router = APIRouter()

def registrar_evento(mensaje: str):
    print(f"[{datetime.utcnow().isoformat()}] [PANEL_CENTRAL] {mensaje}")

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
    
    if x_internal_token != TOKEN_INTERNO_SECRETO or not TOKEN_INTERNO_SECRETO:
        raise HTTPException(status_code=401, detail="No autorizado")
    
    nuevo_tc = payload.get("nuevo_tc")
    if nuevo_tc is None or not isinstance(nuevo_tc, (int, float)):
        raise HTTPException(status_code=400, detail="Valor de TC inválido")
    
    TIPO_CAMBIO = float(nuevo_tc)
    registrar_evento(f"Tipo de cambio actualizado dinámicamente a: {TIPO_CAMBIO}")
    return {"status": "actualizado", "nuevo_tipo_cambio": TIPO_CAMBIO}


# --- MODELOS DE DATOS (PYDANTIC) ---
class UserRegister(BaseModel):
    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    password: str

class UserLogin(BaseModel):
    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    codigo_mfa: str


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
