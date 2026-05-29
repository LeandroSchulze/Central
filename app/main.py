from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Usamos importación relativa con un punto (.) para evitar problemas de PATH en Railway
from database import BasePanel, engine_panel
from routers import metrics, auth, ai_advisor

# Creamos las tablas locales en tu base del Panel si no existen (como la de historial)
BasePanel.metadata.create_all(bind=engine_panel)

app = FastAPI(
    title="Torre de Control SaaS - Backend Exclusivo",
    description="Panel centralizado de monitoreo para AlertTrail y ComplianceFlow"
)

# Configuramos CORS por si vas a consumir el backend desde un dominio de frontend distinto o local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción podés limitar esto a tu URL específica del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inyección de módulos cargados de forma relativa
app.include_router(auth.router)
app.include_router(metrics.router)
app.include_router(ai_advisor.router)

@app.get("/")
def root():
    return {"status": "Online", "sistema": "Torre de Control Ejecutiva"}
