from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

@router.get("/status")
def auth_status():
    return {"status": "Modulo de rutas de autenticacion acoplado correctamente"}
