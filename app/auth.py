from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
import pyotp
import os

# Configuración de cifrado y tokens
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "secret_por_defecto")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # Expiración corta para máxima seguridad
MFA_SECRET = os.getenv("SECRET_MFA_PANEL") # Llave inalterable de 32 caracteres

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

# Simulamos las credenciales del único usuario administrador (Vos) guardadas de forma segura
# En producción, esto se consulta en la tabla de tu base del panel.
ADMIN_USER = "admin_exclusivo"
# Este hash equivale a la contraseña simulada: "PasswordSegura123"
ADMIN_PASSWORD_HASH = "$2b$12$6k62kGZ9Z3nFf.R9tG/nre8o9MhV6G1A.vHwE68yBqg8m1rLleN0m" 

def verificar_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def crear_token_acceso(data: dict):
    datos_copia = data.copy()
    expiracion = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    datos_copia.update({"exp": expiracion})
    return jwt.encode(datos_copia, JWT_SECRET, algorithm=JWT_ALGORITHM)

# Endpoint de Login con Doble Factor (MFA)
@router.post("/login")
def login(username: str, password: str, mfa_code: str):
    # 1. Validar Usuario y Contraseña
    if username != ADMIN_USER or not verificar_password(password, ADMIN_PASSWORD_HASH):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )
    
    # 2. Validar el token de Google Authenticator de 6 dígitos
    totp = pyotp.TOTP(MFA_SECRET)
    if not totp.verify(mfa_code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código de autenticación dinámico (MFA) inválido o expirado"
        )
    
    # 3. Generar el JWT si todo está OK
    token_acceso = crear_token_acceso(data={"sub": username})
    return {"access_token": token_acceso, "token_type": "bearer"}

# Dependencia de seguridad para proteger los endpoints
def verificar_usuario_actual(token: str = Depends(oauth2_scheme)):
    credenciales_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales de acceso",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username != ADMIN_USER:
            raise credenciales_exception
        return username
    except JWTError:
        raise credenciales_exception
