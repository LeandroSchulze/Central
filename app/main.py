from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# AHROA SÍ: Usamos importación relativa con un punto (.) para decirle a Python 
# que busque el archivo exactamente en esta misma carpeta actual
from .database import BasePanel, engine_panel
from .routers import metrics, auth, ai_advisor

# Creamos las tablas locales en tu base del Panel si no existen
BasePanel.metadata.create_all(bind=engine_panel)

app = FastAPI(
    title="Torre de Control SaaS - Backend Exclusivo",
    description="Panel centralizado de monitoreo para AlertTrail y ComplianceFlow"
)

# Corregido: add_middleware debe ser llamado desde el objeto app.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Corregido: include_router debe ser llamado desde el objeto app.
app.include_router(auth.router)
app.include_router(metrics.router)
app.include_router(ai_advisor.router)

@app.get("/")
def root():
    return {"status": "Online", "sistema": "Torre de Control Ejecutiva"}
