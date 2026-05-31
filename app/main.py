from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Esto ahora va a funcionar porque database.py sí va a existir acá
from app.database import BasePanel, engine_panel
from app.routers import metrics, auth, ai_advisor

BasePanel.metadata.create_all(bind=engine_panel)

app = FastAPI(
    title="Torre de Control SaaS - Backend Exclusivo",
    description="Panel centralizado de monitoreo para AlertTrail y ComplianceFlow"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(metrics.router)
app.include_router(ai_advisor.router)

@app.get("/")
def root():
    return {"status": "Online", "sistema": "Torre de Control Ejecutiva"}
