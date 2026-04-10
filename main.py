from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import models
from database import engine
from routers import sucursales, usuarios, pedidos, archivos
from fastapi.middleware.cors import CORSMiddleware

# ¡Magia! Esta línea revisa tus modelos y crea las tablas en PostgreSQL si no existen
models.Base.metadata.create_all(bind=engine)

# Inicializamos la aplicación
app = FastAPI() # Esta línea ya la tienes

# --- NUEVO: Darle permiso al Frontend (CORS) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # El "*" significa "deja pasar a todos" (perfecto para pruebas)
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)
# -----------------------------------------------

# Configuración de CORS (Cross-Origin Resource Sharing)
# Esto es vital para que el Frontend separado pueda hacerle peticiones a este Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Nota: En producción cambiaremos el "*" por la URL real de Vercel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(sucursales.router)
app.include_router(usuarios.router) 
app.include_router(pedidos.router)
app.include_router(archivos.router)


# Creamos nuestra primera ruta de prueba
@app.get("/")
def ruta_raiz():
    return {"mensaje": "¡El servidor de Pedidos Acero está vivo y corriendo sin trabas!"}