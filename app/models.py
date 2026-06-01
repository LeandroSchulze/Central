from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

# IMPORTACIÓN DE LA BASE DEL PANEL CON RUTA ABSOLUTA REAL
from app.database import BasePanel

class HistorialMetricas(BasePanel):
    __tablename__ = "historial_metricas"

    id = Column(Integer, primary_key=True, index=True)
    sistema = Column(String, index=True)          
    tipo_metrica = Column(String, index=True)     
    valor = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    detalles = Column(String, nullable=True)
