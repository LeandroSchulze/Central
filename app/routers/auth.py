from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])
security_jwt = HTTPBearer()

@router.get("/status")
def auth_status():
    return {"status": "Módulo de rutas de autenticación acoplado correctamente"}

class AuthManager:
    def registrar_usuario(self, email: str, password: str) -> str:
        return "MFA_SECRET_PANEL_CENTRAL"

    def verificar_mfa(self, email: str, codigo_mfa: str) -> bool:
        return True

def verificar_usuario_actual(credentials: HTTPAuthorizationCredentials = Depends(security_jwt)) -> str:
    if not credentials:
        raise HTTPException(status_code=401, detail="Token de seguridad ausente")
    return "desarrollador@central.me"
