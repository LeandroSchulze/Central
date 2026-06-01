import os
import sys
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
import requests
import json

# 🔥 INYECCIÓN DE SEGURIDAD PARA EVITAR CRASHES DE RUTAS EN RAILWAY
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# IMPORTACIONES PLANAS CORREGIDAS (Sin el prefijo app.)
from database import get_db_panel, get_db_alerttrail, get_db_compliance
from models import HistorialMetricas

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
    at_crecimiento_pct = 0.0
    cf_crecimiento_pct = 0.0

    # Bloque seguro para evitar que inconsistencias en el mapeo histórico rompan el dashboard
    try:
        # Buscamos la foto de hace 30 días tolerando tanto la columna 'timestamp' como 'fecha'
        foto_pasada = db_panel.query(HistorialMetricas).filter(
            text("DATE(timestamp) = :fecha_pasada OR DATE(fecha) = :fecha_pasada")
        ).params(fecha_pasada=hace_un_mes).first()

        if foto_pasada:
            # Leemos de forma segura los atributos por si aún usás filas mapeadas en vez de columnas directas
            at_usuarios_pasados = getattr(foto_pasada, "alerttrail_usuarios_totales", 0)
            cf_usuarios_pasados = getattr(foto_pasada, "compliance_usuarios_totales", 0)

            if at_usuarios_pasados > 0:
                at_crecimiento_pct = ((at_totales - at_usuarios_pasados) / at_usuarios_pasados) * 100
                
            if cf_usuarios_pasados > 0:
                cf_crecimiento_pct = ((cf_totales - cf_usuarios_pasados) / cf_usuarios_pasados) * 100
    except Exception as e:
        print(f"[{datetime.utcnow().isoformat()}] [METRICS_WARNING] Variación mensual omitida por estructura de tabla: {str(e)}")

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
