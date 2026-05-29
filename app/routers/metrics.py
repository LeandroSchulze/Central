from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
import requests
import json

from app.database import get_db_panel, get_db_alerttrail, get_db_compliance
from app.models import HistorialMetricas

router = APIRouter(prefix="/api/v1/metrics", tags=["Metrics"])

# Función auxiliar para obtener el Tipo de Cambio (TC) oficial en Argentina
def obtener_tipo_cambio():
    try:
        # Consumimos una API pública y estable de cotización (Dólar Tarjeta/Oficial)
        url = "https://dolarapi.com/v1/dolares/oficial"
        respuesta = requests.get(url, timeout=5)
        if respuesta.status_code == 200:
            return respuesta.json().get("venta", 1.0)
    except Exception:
        pass
    return 1000.0  # Valor de respaldo por si falla la API externa

@router.get("/dashboard")
def obtener_dashboard_completo(
    db_panel: Session = Depends(get_db_panel),
    db_alerttrail: Session = Depends(get_db_alerttrail),
    db_compliance: Session = Depends(get_db_compliance)
):
    tc = obtener_tipo_cambio()
    hoy = datetime.utcnow().date()
    hace_un_mes = hoy - timedelta(days=30)

    # ==========================================
    # 1. MÉTRICAS DE ALERTTRAIL
    # ==========================================
    # Total usuarios (Campos id/user_id)
    at_totales = db_alerttrail.execute(text("SELECT COUNT(id) FROM usuarios")).scalar() or 0
    # Nuevos usuarios hoy (asumiendo campo creado_en / created_at)
    at_nuevos_hoy = db_alerttrail.execute(
        text("SELECT COUNT(id) FROM usuarios WHERE DATE(created_at) = :hoy"), {"hoy": hoy}
    ).scalar() or 0
    
    # Conteo de suscripciones activas (revisadas por tu Scheduler a medianoche)
    at_premium_activos = db_alerttrail.execute(
        text("SELECT COUNT(id) FROM suscripciones WHERE estado = 'activo'")
    ).scalar() or 0

    # ==========================================
    # 2. MÉTRICAS DE COMPLIANCEFLOW
    # ==========================================
    # Total usuarios (Primary Key es el email corporativo)
    cf_totales = db_compliance.execute(text("SELECT COUNT(email) FROM usuarios")).scalar() or 0
    cf_nuevos_hoy = db_compliance.execute(
        text("SELECT COUNT(email) FROM usuarios WHERE DATE(creado_en) = :hoy"), {"hoy": hoy}
    ).scalar() or 0
    
    # Conteo de planes en Compliance (Pase Express y Licencia Enterprise + Copiloto IA)
    cf_express = db_compliance.execute(
        text("SELECT COUNT(email) FROM usuarios WHERE plan_activo = 'express'")
    ).scalar() or 0
    cf_enterprise = db_compliance.execute(
        text("SELECT COUNT(email) FROM usuarios WHERE plan_activo = 'enterprise'")
    ).scalar() or 0

    # ==========================================
    # 3. CÁLCULO DE VARIACIONES (%) HISTÓRICAS
    # ==========================================
    # Buscamos la foto de hace 30 días en la base del Panel
    foto_pasada = db_panel.query(HistorialMetricas).filter(
        text("DATE(fecha) = :fecha_pasada")
    ).params(fecha_pasada=hace_un_mes).first()

    at_crecimiento_pct = 0.0
    cf_crecimiento_pct = 0.0

    if foto_pasada and foto_pasada.alerttrail_usuarios_totales > 0:
        at_crecimiento_pct = ((at_totales - foto_pasada.alerttrail_usuarios_totales) / foto_pasada.alerttrail_usuarios_totales) * 100
        
    if foto_pasada and foto_pasada.compliance_usuarios_totales > 0:
        cf_crecimiento_pct = ((cf_totales - foto_pasada.compliance_usuarios_totales) / foto_pasada.compliance_usuarios_totales) * 100

    # Estimación de Ingresos unificados (multiplicando los dólares de Compliance por el TC)
    ingresos_usd_cf = (cf_express * 20) + (cf_enterprise * 50)
    ingresos_ars_cf_estimados = ingresos_usd_cf * tc

    return {
        "tipo_cambio": tc,
        "fecha_reporte": hoy.isoformat(),
        "alerttrail": {
            "usuarios_totales": at_totales,
            "nuevos_hoy": at_nuevos_hoy,
            "crecimiento_mensual_pct": round(at_crecimiento_pct, 2),
            "planes_activos": {
                "premium": at_premium_activos
            }
        },
        "complianceflow": {
            "usuarios_totales": cf_totales,
            "nuevos_hoy": cf_nuevos_hoy,
            "crecimiento_mensual_pct": round(cf_crecimiento_pct, 2),
            "planes_activos": {
                "pase_express_20usd": cf_express,
                "enterprise_copiloto_50usd": cf_enterprise
            },
            "facturacion_estimada_ars": round(ingresos_ars_cf_estimados, 2)
        }
    }
