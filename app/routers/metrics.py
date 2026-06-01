from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
import requests

# IMPORTACIONES CONFIGURADAS CON LA RUTA ABSOLUTA CORRECTA
from app.database import get_db_panel, get_db_alerttrail, get_db_compliance
from app.models import HistorialMetricas

router = APIRouter(prefix="/api/v1/metrics", tags=["Metrics"])

def obtener_tipo_cambio():
    try:
        url = "https://dolarapi.com/v1/dolares/oficial"
        respuesta = requests.get(url, timeout=5)
        if respuesta.status_code == 200:
            return respuesta.json().get("venta", 1.0)
    except Exception:
        pass
    return 1000.0

@router.get("/dashboard")
def obtener_dashboard_completo(
    db_panel: Session = Depends(get_db_panel),
    db_alerttrail: Session = Depends(get_db_alerttrail),
    db_compliance: Session = Depends(get_db_compliance)
):
    tc = obtener_tipo_cambio()
    hoy = datetime.utcnow().date()
    hace_un_mes = hoy - timedelta(days=30)

    # 1. Metrics AlertTrail
    at_totales = db_alerttrail.execute(text("SELECT COUNT(id) FROM usuarios")).scalar() or 0
    at_nuevos_hoy = db_alerttrail.execute(
        text("SELECT COUNT(id) FROM usuarios WHERE DATE(created_at) = :hoy"), {"hoy": hoy}
    ).scalar() or 0
    at_premium_activos = db_alerttrail.execute(
        text("SELECT COUNT(id) FROM suscripciones WHERE estado = 'activo'")
    ).scalar() or 0

    # 2. Metrics ComplianceFlow
    cf_totales = db_compliance.execute(text("SELECT COUNT(email) FROM usuarios")).scalar() or 0
    cf_nuevos_hoy = db_compliance.execute(
        text("SELECT COUNT(email) FROM usuarios WHERE DATE(creado_en) = :hoy"), {"hoy": hoy}
    ).scalar() or 0
    cf_express = db_compliance.execute(
        text("SELECT COUNT(email) FROM usuarios WHERE plan_activo = 'express'")
    ).scalar() or 0
    cf_enterprise = db_compliance.execute(
        text("SELECT COUNT(email) FROM usuarios WHERE plan_activo = 'enterprise'")
    ).scalar() or 0

    # 3. Datos Históricos
    at_crecimiento_pct = 0.0
    cf_crecimiento_pct = 0.0

    try:
        foto_pasada = db_panel.query(HistorialMetricas).filter(
            text("DATE(timestamp) = :fecha_pasada OR DATE(fecha) = :fecha_pasada")
        ).params(fecha_pasada=hace_un_mes).first()

        if foto_pasada:
            at_usuarios_pasados = getattr(foto_pasada, "alerttrail_usuarios_totales", 0)
            cf_usuarios_pasados = getattr(foto_pasada, "compliance_usuarios_totales", 0)

            if at_usuarios_pasados > 0:
                at_crecimiento_pct = ((at_totales - at_usuarios_pasados) / at_usuarios_pasados) * 100
                
            if cf_usuarios_pasados > 0:
                cf_crecimiento_pct = ((cf_totales - cf_usuarios_pasados) / cf_usuarios_pasados) * 100
    except Exception as e:
        print(f"[{datetime.utcnow().isoformat()}] [METRICS_WARNING] Historial omitido de forma segura: {str(e)}")

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
