import os
from sqlalchemy import create_all, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Obtenemos la URL de conexión de PostgreSQL desde las variables de entorno de Railway
# (Por seguridad y buenas prácticas, siempre usando os.getenv)
DATABASE_URL = os.getenv("DATABASE_URL")

# Un pequeño fallback por si estás probando algo local, pero en Railway usará la variable de arriba
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/torre_control"

# Si la URL empieza con 'postgres://' (común en Railway/Heroku), la adaptamos a 'postgresql://' 
# porque SQLAlchemy 1.4+ requiere el nombre completo del dialecto.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 2. Creamos el motor de conexión (Engine) para tu Panel Centralizado
engine_panel = create_engine(
    DATABASE_URL,
    pool_pre_ping=True  # Evita errores de conexiones caídas (muy recomendado en Railway)
)

# 3. Creamos la fábrica de sesiones para interactuar con la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_panel)

# 4. Definimos la Base Declarativa que heredarán tus modelos del Panel (como el historial)
BasePanel = declarative_base()

# 5. Dependencia útil para tus endpoints (FastAPI Dependency) por si necesitás usar la DB en los routers
def get_db_panel():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
