# app/auth.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

security_jwt = HTTPBearer()

@router.get("/status")
def auth_status():
    return {"status": "Módulo de rutas de autenticación acoplado correctamente"}

class AuthManager:
    def registrar_usuario(self, email: str, password: str) -> str:
        # Placeholder del secreto MFA para no romper el main.py
        return "MFA_SECRET_PROVISORIO"

    def verificar_mfa(self, email: str, codigo_mfa: str) -> bool:
        # Retorna True por defecto para pruebas temporales
        return True

def verificar_usuario_actual(credentials: HTTPAuthorizationCredentials = Depends(security_jwt)) -> str:
    # Validador provisorio para que el módulo de IA no se bloquee sin un token real
    if not credentials:
        raise HTTPException(status_code=401, detail="Token no proporcionado")
    return "desarrollador_solo@central.me"
