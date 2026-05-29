from fastapi import APIRouter, Depends, HTTPException
import requests
import os
import json

from app.routers.metrics import obtener_dashboard_completo, obtener_tipo_cambio
from app.database import get_db_panel, get_db_alerttrail, get_db_compliance
from app.auth import verificar_usuario_actual

router = APIRouter(prefix="/api/v1/ai", tags=["AI Advisor"])

# Simulamos la estructura exacta del diccionario maestro que tenés corriendo en el main.py de ComplianceFlow
# Así la IA sabe exactamente qué está pasando con las normativas técnicas sin necesidad de persistirlas en Postgres.
DATA_ESTANDARES_COMPLIANCE = {
    "ISO-IAM": {
        "norma": "ISO 27001 — Anexo A.9",
        "titulo": "Auditoría de Control de Accesos",
        "evidencia_id": "EV-ISO-A9-8812",
        "estado": "⚠️ OBSERVACIÓN DETECTADA",
        "detalle": "Políticas AdministratorAccess asignadas a cuentas de desarrollo sin MFA activo."
    },
    "SOC2-S3": {
        "norma": "SOC 2 Type II — CC6.3",
        "titulo": "Análisis Criptográfico S3",
        "evidencia_id": "EV-SOC2-S3-9202",
        "estado": "🟢 100% CUMPLIDO",
        "detalle": "Public Access Block activo y cifrado SSE-S3 de forma persistente."
    },
    "ISO-9001": {
        "norma": "ISO 9001 — Cláusula 8.2",
        "titulo": "Trazabilidad de Requisitos de Calidad",
        "evidencia_id": "EV-ISO9-QA-3321",
        "estado": "🟢 100% CUMPLIDO",
        "detalle": "Pipeline CI/CD automatizado con aprobación cruzada digital firmada por control de calidad."
    },
    "SOC1-FIN": {
        "norma": "SOC 1 — Controles ICFR",
        "titulo": "Matriz de Segregación de Funciones",
        "evidencia_id": "EV-SOC1-FIN-7741",
        "estado": "🟢 100% CUMPLIDO",
        "detalle": "Firmas transaccionales de balances contables desacopladas de cuentas de desarrollo."
    }
} [cite: 18, 19, 20, 21, 22, 23, 24]

@router.get("/insights")
def obtener_analisis_ia(
    db_panel = Depends(get_db_panel),
    db_alerttrail = Depends(get_db_alerttrail),
    db_compliance = Depends(get_db_compliance),
    usuario_verificado: str = Depends(verificar_usuario_actual) # <--- Candado de seguridad JWT
):
    # 1. Recuperamos la foto actual del negocio llamando a la lógica del dashboard
    metricas_negocio = obtener_dashboard_completo(db_panel, db_alerttrail, db_compliance)
    
    # 2. Consolidamos todo el contexto en un único payload estructurado para enviarle a la IA
    contexto_sistema = {
        "metricas_negocio_saas": metricas_negocio,
        "estado_normativas_complianceflow": DATA_ESTANDARES_COMPLIANCE
    }
    
    # 3. Diseñamos el Prompt del sistema con instrucciones híper-específicas de rol
    prompt_sistema = (
        "Sos un consultor experto en optimización de plataformas de Software as a Service (SaaS), "
        "ciberseguridad y análisis de datos de negocio. Analizá el siguiente reporte técnico y de "
        "negocio de mis dos aplicaciones individuales: AlertTrail y ComplianceFlow.\n\n"
        f"DATOS DE ENTRADA:\n{json.dumps(contexto_sistema, indent=2)}\n\n"
        "TAREA EXCLUSIVA:\n"
        "Identificá anomalías, fallas en el comportamiento del negocio (por ejemplo, estancamiento de "
        "usuarios o caída de planes) y riesgos de seguridad técnicos basándote en los estados informados.\n"
        "Devolvé un análisis conciso estructurado estrictamente con este formato:\n"
        "- 🚨 ALERTAS/FALLAS DETECTADAS: (Si hay anomalías en el negocio o riesgos técnicos como estados de observación).\n"
        "- 📈 RECOMENDACIONES DE MEJORA: (Acciones concretas para optimizar la conversión, retención o corregir infraestructura).\n"
        "Sé directo, técnico y al grano. Hablá en español neutro o rioplatense."
    )
    
    # 4. Consumimos el endpoint de la API de Inteligencia Artificial (Ejemplo usando la API de Gemini)
    api_key = os.getenv("AI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Falta configurar la variable de entorno AI_API_KEY")
        
    url_api = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload_ia = {
        "contents": [{
            "parts": [{"text": prompt_sistema}]
        }]
    }
    
    try:
        respuesta = requests.post(url_api, json=payload_ia, headers=headers, timeout=10)
        if respuesta.status_code != 200:
            raise HTTPException(status_code=502, detail="Error en la respuesta del motor de Inteligencia Artificial")
            
        resultado_json = respuesta.json()
        # Extraemos el texto crudo retornado por el LLM
        insights_texto = resultado_json['candidates'][0]['content']['parts'][0]['text']
        
        return {
            "estado": "exitoso",
            "analisis_ia": insights_texto
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falla al conectar con el servicio de IA: {str(e)}")
