from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from app.database import BasePanel

class HistorialMetricas(BasePanel):
    __tablename__ = "historial_metricas"

    id = Column(Integer, primary_key=True, index=True)
    sistema = Column(String, index=True)          # Para diferenciar si es de AlertTrail o ComplianceFlow
    tipo_metrica = Column(String, index=True)     # 'cpu', 'ram', 'alertas_bloqueadas', 'pagos_procesados', etc.
    valor = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    detalles = Column(String, nullable=True)       # Un campo de texto extra por las dudas
