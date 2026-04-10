import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# 1. Cargar las variables de entorno desde el archivo .env
load_dotenv()

# 2. Obtener la URL de la base de datos de forma segura
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# 3. Validar que la variable exista (buena práctica para evitar caídas silenciosas)
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("¡Error! No se encontró DATABASE_URL en el archivo .env")

# 4. Configurar el motor de la base de datos
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 5. Crear la sesión local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 6. Clase base para los modelos
Base = declarative_base()

# 7. Dependencia para inyectar la base de datos en las rutas de FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()