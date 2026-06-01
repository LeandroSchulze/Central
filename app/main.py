import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, status, APIRouter, Header
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

# IMPORTACIONES ABSOLUTAS REALES BASADAS EN TU CARPETA 'ROUTERS'
from app.routers.auth import AuthManager, router as auth_router
from app.routers.metrics import router as metrics_router
from app.routers.ai_advisor import router as ai_router

load_dotenv()

app = FastAPI(
    title="Torre de Control Central",
    description="Panel unificado para monitoreo de usuarios, pagos y métricas de AlertTrail y ComplianceFlow.",
    version="1.0.0"
)

auth_handler = AuthManager()
router = APIRouter()

def registrar_evento_local(mensaje: str):
    print(f"[{datetime.utcnow().isoformat()}] [PANEL_CENTRAL] {mensaje}")

# ==========================================
# CÓDIGO DE CONTROL DE TIPO DE CAMBIO (IA)
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
    registrar_evento_local(f"Tipo de cambio actualizado dinámicamente a: {TIPO_CAMBIO}")
    return {"status": "actualizado", "nuevo_tipo_cambio": TIPO_CAMBIO}


class UserRegister(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    codigo_mfa: str


# --- VISTAS HTML ---
@app.get("/", response_class=HTMLResponse)
def index(): 
    return FileResponse("templates/index.html")

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(): 
    return FileResponse("templates/dashboard.html")

@app.get("/login", response_class=HTMLResponse)
def mostrar_login(): 
    return FileResponse("templates/login.html")


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


# Inyección de routers del ecosistema
app.include_router(router)
app.include_router(metrics_router)
app.include_router(ai_router)
app.include_router(auth_router)
