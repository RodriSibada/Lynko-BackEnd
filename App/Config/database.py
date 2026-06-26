from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configuración de conexión a PostgreSQL
DATABASE_URL = DATABASE_URL = "postgresql://postgres:password@localhost:5432/lynko_nueva"

# Crear engine
engine = create_engine(DATABASE_URL, echo=True)

# Session local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()

# Dependency para obtener DB en rutas
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()