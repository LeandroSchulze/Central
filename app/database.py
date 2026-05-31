import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Obtenemos la URL de conexión de PostgreSQL desde las variables de entorno de Railway
DATABASE_URL = os.getenv("DATABASE_URL")

# Fallback por si probás algo local
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/torre_control"

# Adaptamos 'postgres://' a 'postgresql://' requerido por SQLAlchemy 1.4+
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 2. Creamos el motor de conexión (Engine) para tu Panel Centralizado
engine_panel = create_engine(
    DATABASE_URL,
    pool_pre_ping=True  # Evita errores de conexiones caídas en Railway
)

# 3. Creamos la fábrica de sesiones para interactuar con la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_panel)

# 4. Definimos la Base Declarativa que heredarán tus modelos del Panel
BasePanel = declarative_base()

# 5. Dependencia útil para tus endpoints del Panel Central
def get_db_panel():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------------------------------------------------------------
# 🚀 DEPENDENCIAS INTERNAS REQUERIDAS POR TU ROUTER DE MÉTRICAS (metrics.py)
# -----------------------------------------------------------------------------------

# Mapea la sesión requerida para AlertTrail usando el mismo pool estable
def get_db_alerttrail():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Mapea la sesión requerida para ComplianceFlow usando el mismo pool estable
def get_db_compliance():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
