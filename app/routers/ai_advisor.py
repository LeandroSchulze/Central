# app/ai_advisor.py
from fastapi import APIRouter, Depends, HTTPException
import requests
import os
import json

# CORRECCIÓN: Importación directa desde app.metrics sin la subcarpeta 'routers'
from app.metrics import obtener_dashboard_completo, obtener_tipo_cambio
from app.database import get_db_panel, get_db_alerttrail, get_db_compliance
from app.auth import verificar_usuario_actual

router = APIRouter(prefix="/api/v1/ai", tags=["AI Advisor"])

DATA_ESTANDARES_COMPLIANCE = {
    "ISO-IAM": {
        "norma": "ISO 27001 — Anexo A.9",
        "titulo": "Auditoría de Control de Accesos",
        "evidencia_id": "EV-ISO-A9-8812",
        "estado": "⚠️ OBSERVACIÓN DETECTADA",
        "detail": "Políticas AdministratorAccess asignadas a cuentas de desarrollo sin MFA activo."
    },
    "SOC2-S3": {
        "norma": "SOC 2 Type II — CC6.3",
        "titulo": "Análisis Criptográfico S3",
        "evidencia_id": "EV-SOC2-S3-9202",
        "estado": "🟢 100% CUMPLIDO",
        "detail": "Public Access Block activo y cifrado SSE-S3 de forma persistente."
    }
}

@router.get("/insights")
def obtener_analisis_ia(
    db_panel = Depends(get_db_panel),
    db_alerttrail = Depends(get_db_alerttrail),
    db_compliance = Depends(get_db_compliance),
    usuario_verificado: str = Depends(verificar_usuario_actual)
):
    metricas_negocio = obtener_dashboard_completo(db_panel, db_alerttrail, db_compliance)
    
    contexto_sistema = {
        "metricas_negocio_saas": metricas_negocio,
        "estado_normativas_complianceflow": DATA_ESTANDARES_COMPLIANCE
    }
    
    prompt_sistema = (
        "Sos un consultor experto en optimización de plataformas SaaS y métricas de negocio. "
        "Analizá el siguiente reporte consolidado de AlertTrail y ComplianceFlow:\n\n"
        f"{json.dumps(contexto_sistema, indent=2)}\n\n"
        "Devolvé un análisis conciso estructurado estrictamente con este formato:\n"
        "- 🚨 ALERTAS/FALLAS DETECTADAS\n"
        "- 📈 RECOMENDACIONES DE MEJORA\n"
        "Hablá en español."
    )
    
    api_key = os.getenv("AI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Falta configurar la variable de entorno AI_API_KEY")
        
    url_api = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload_ia = {"contents": [{"parts": [{"text": prompt_sistema}]}]}
    
    try:
        respuesta = requests.post(url_api, json=payload_ia, headers=headers, timeout=10)
        if respuesta.status_code != 200:
            raise HTTPException(status_code=502, detail="Error en la respuesta del motor de IA")
            
        resultado_json = respuesta.json()
        insights_texto = resultado_json['candidates'][0]['content']['parts'][0]['text']
        
        return {
            "estado": "exitoso",
            "analisis_ia": insights_texto,
            "tipo_cambio_aplicado": metricas_negocio["tipo_cambio"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falla al conectar con el servicio de IA: {str(e)}")
