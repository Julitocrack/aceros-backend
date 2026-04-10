from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# ==========================
# ESQUEMAS PARA SUCURSALES
# ==========================
class SucursalBase(BaseModel):
    nombre: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    tiene_produccion: bool = False # <--- ¡AQUÍ ESTÁ EL CAMBIO!

class SucursalCreate(SucursalBase):
    pass # Para crear, pedimos lo mismo que el Base

class Sucursal(SucursalBase):
    id: int

    class Config:
        from_attributes = True # Esto permite leer los datos de SQLAlchemy

# ==========================
# ESQUEMAS PARA USUARIOS
# ==========================
class UsuarioBase(BaseModel):
    nombre_completo: str
    username: str
    rol: str
    sucursal_id: Optional[int] = None

class UsuarioCreate(UsuarioBase):
    password: str # Solo pedimos la contraseña al crearlo

class Usuario(UsuarioBase):
    id: int
    # ¡OJO! No incluimos la contraseña aquí por seguridad

    class Config:
        from_attributes = True

# ==========================
# ESQUEMAS PARA PEDIDOS
# ==========================
class PedidoBase(BaseModel):
    url_foto_ticket: str
    notas: Optional[str] = None

class PedidoCreate(PedidoBase):
    # Cuando la vendedora crea un pedido, solo manda la foto y las notas.
    pass 

# NUEVO: El paquete de datos exacto que mandará la dueña al aprobar
class PedidoAprobar(BaseModel):
    estado: str # Aquí mandará "Aprobado"
    requiere_produccion: bool # El switch que prenderá o apagará
    sucursal_destino_id: int # La bodega a donde lo manda

# NUEVO: Para Producción y Logística (ellos solo mueven el estado, no deciden destino)
class PedidoEstadoUpdate(BaseModel):
    estado: str

# La respuesta completa que devuelve la API
class Pedido(PedidoBase):
    id: int
    estado: str
    fecha_creacion: datetime
    fecha_aprobacion: Optional[datetime] = None # <--- AGREGA ESTO
    requiere_produccion: bool
    sucursal_id: int
    sucursal_destino_id: Optional[int] = None
    creador_id: int
    tipo_orden: str
    numero_ticket: Optional[str] = None

    class Config:
        from_attributes = True