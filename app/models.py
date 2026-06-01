import os
import sys
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

# 🔥 INYECCIÓN DE SEGURIDAD PARA EVITAR CRASHES DE RUTAS EN RAILWAY
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# IMPORTACIÓN PLANA CORREGIDA (Sin el prefijo app.)
from database import BasePanel

class HistorialMetricas(BasePanel):
    __tablename__ = "historial_metricas"

    id = Column(Integer, primary_key=True, index=True)
    sistema = Column(String, index=True)          # Para diferenciar si es de AlertTrail o ComplianceFlow
    tipo_metrica = Column(String, index=True)     # 'cpu', 'ram', 'alertas_bloqueadas', 'pagos_procesados', etc.
    valor = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    detalles = Column(String, nullable=True)       # Un campo de texto extra por las dudas
