from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])
security_jwt = HTTPBearer()

@router.get("/status")
def auth_status():
    return {"status": "Modulo de rutas de autenticacion acoplado correctamente"}

class AuthManager:
    def registrar_usuario(self, email: str, password: str) -> str:
        return "MFA_SECRET_BASE_DEVELOPER"

    def verificar_mfa(self, email: str, codigo_mfa: str) -> bool:
        return True

def verificar_usuario_actual(credentials: HTTPAuthorizationCredentials = Depends(security_jwt)) -> str:
    if not credentials:
        raise HTTPException(status_code=401, detail="Token no proporcionado")
    return "developer@central.me"
