from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from database import Base
import datetime

class Sucursal(Base):
    __tablename__ = "sucursales"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True, nullable=False)
    direccion = Column(String, nullable=True)
    telefono = Column(String, nullable=True)

    tiene_produccion = Column(Boolean, default=False)

    # Relación: Una sucursal tiene muchos usuarios y muchos pedidos
    usuarios = relationship("Usuario", back_populates="sucursal")
    pedidos = relationship("Pedido", back_populates="sucursal", foreign_keys="[Pedido.sucursal_id]")


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre_completo = Column(String, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    rol = Column(String, nullable=False) # Roles: 'duena', 'sucursal', 'almacen'
    
    # Llave foránea para saber a qué sucursal pertenece
    sucursal_id = Column(Integer, ForeignKey("sucursales.id"), nullable=True)

    # Relaciones
    sucursal = relationship("Sucursal", back_populates="usuarios")
    pedidos_creados = relationship("Pedido", back_populates="creador")


class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    # Estados: Pendiente, Aprobado, En_Produccion, En_Logistica, Entregado
    estado = Column(String, default="Pendiente") 
    tipo_orden = Column(String, default="Venta")
    numero_ticket = Column(String, nullable=True)
    url_foto_ticket = Column(String, nullable=False)
    notas = Column(Text, nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)
    fecha_aprobacion = Column(DateTime, nullable=True)

    # Campo nuevo: Para saber si pasa por taller de cortes o va directo a camiones
    requiere_produccion = Column(Boolean, default=False)

    # Llaves foráneas
    # 1. Sucursal de origen (donde la vendedora toma la foto)
    sucursal_id = Column(Integer, ForeignKey("sucursales.id"), nullable=False)
    
    # 2. Sucursal de destino (donde la dueña manda surtir el acero)
    # Es nullable=True porque al inicio, cuando es "Pendiente", aún no se asigna
    sucursal_destino_id = Column(Integer, ForeignKey("sucursales.id"), nullable=True)
    
    # 3. Quién creó el registro (la vendedora)
    creador_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    sucursal = relationship("Sucursal", foreign_keys=[sucursal_id], back_populates="pedidos")
    sucursal_destino = relationship("Sucursal", foreign_keys=[sucursal_destino_id])
    creador = relationship("Usuario", back_populates="pedidos_creados")