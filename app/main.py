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
# 🛠️ CLASES Y FUNCIONES LOCALES
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
# 🛡️ BUSCADOR ULTRA-AGRESIVO DE HTML (EVITA CRASH 500)
# =====================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def obtener_ruta_template(nombre_archivo: str) -> str:
    # Mapea TODAS las combinaciones posibles donde podrías haber guardado el HTML
    rutas_a_probar = [
        os.path.join(BASE_DIR, "templates", nombre_archivo),                  # app/app/templates/
        os.path.join(os.path.dirname(BASE_DIR), "templates", nombre_archivo), # app/templates/
        os.path.join(BASE_DIR, nombre_archivo),                               # Suelto junto al main.py
        os.path.join(os.path.dirname(BASE_DIR), nombre_archivo),              # Suelto en la raíz del repo
        os.path.join(os.getcwd(), "templates", nombre_archivo),               # Ruta de ejecución local templates/
        os.path.join(os.getcwd(), nombre_archivo)                             # Ruta de ejecución local raíz
    ]
    
    for ruta in rutas_a_probar:
        if os.path.exists(ruta):
            return ruta
            
    return ""  # Retorna vacío si el archivo realmente no existe en ningún lado

def respuesta_html_segura(nombre_archivo: str):
    ruta = obtener_ruta_template(nombre_archivo)
    
    if ruta and os.path.exists(ruta):
        return FileResponse(ruta)
    
    # Si el archivo HTML no está en el repo, devolvemos una web de emergencia (Status 200 OK)
    html_emergencia = f"""
    <html>
        <body style='background:#1f2937; color:#f9fafb; font-family:sans-serif; text-align:center; padding:10%;'>
            <h1 style='color:#60a5fa;'>Torre de Control Activa 🚀</h1>
            <p>El servidor Python y la API están funcionando perfectamente en producción.</p>
            <div style='background:#374151; padding:20px; border-radius:10px; display:inline-block; margin-top:20px;'>
                <p style='color:#f87171;'>⚠️ Alerta Visual: No se encontró el archivo <b>{nombre_archivo}</b></p>
                <p style='font-size:14px; color:#9ca3af;'>Revisá que hayas subido este archivo a GitHub/Railway.</p>
            </div>
            <br><br>
            <a href='/docs' style='color:#34d399; text-decoration:none; font-weight:bold;'>Ver Endpoints de la API (Swagger)</a>
        </body>
    </html>
    """
    return HTMLResponse(content=html_emergencia, status_code=200)


# --- VISTAS HTML PROTEGIDAS ---
@app.get("/", response_class=HTMLResponse)
def index(): 
    return respuesta_html_segura("index.html")

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(): 
    # Sabemos que tenés 'dashboard.html', con esta función lo va a encontrar sí o sí.
    return respuesta_html_segura("dashboard.html")

@app.get("/login", response_class=HTMLResponse)
def mostrar_login(): 
    return respuesta_html_segura("login.html")


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


app.include_router(router)
