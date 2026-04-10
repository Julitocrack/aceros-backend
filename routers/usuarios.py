from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import bcrypt

import models, schemas
from database import get_db

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"]
)

# Esquema exclusivo para recibir las credenciales del login
class LoginRequest(BaseModel):
    username: str
    password: str

# 1. Crear un nuevo usuario (Actualizado a bcrypt moderno)
@router.post("/", response_model=schemas.Usuario)
def crear_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    # Verificamos que el username no exista ya
    db_usuario = db.query(models.Usuario).filter(models.Usuario.username == usuario.username).first()
    if db_usuario:
        raise HTTPException(status_code=400, detail="El username ya está registrado")
    
    # Encriptamos la contraseña de forma segura
    salt = bcrypt.gensalt()
    hashed_password_bytes = bcrypt.hashpw(usuario.password.encode('utf-8'), salt)
    hashed_password_str = hashed_password_bytes.decode('utf-8')

    nuevo_usuario = models.Usuario(
        nombre_completo=usuario.nombre_completo,
        username=usuario.username,
        hashed_password=hashed_password_str,
        rol=usuario.rol,
        sucursal_id=usuario.sucursal_id
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario

# 2. Obtener lista de todos los usuarios
@router.get("/", response_model=List[schemas.Usuario])
def obtener_usuarios(db: Session = Depends(get_db)):
    usuarios = db.query(models.Usuario).all()
    return usuarios

# 3. Iniciar Sesión (La ruta que conecta con React)
@router.post("/login")
def iniciar_sesion(datos: LoginRequest, db: Session = Depends(get_db)):
    # 1. Buscamos al usuario por su username
    usuario = db.query(models.Usuario).filter(models.Usuario.username == datos.username).first()
    
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
        
    # 2. Convertimos los textos a bytes (formato que exige bcrypt)
    password_bytes = datos.password.encode('utf-8')
    hashed_bytes = usuario.hashed_password.encode('utf-8')
    
    # 3. Verificamos si la contraseña coincide con la encriptada
    if not bcrypt.checkpw(password_bytes, hashed_bytes):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
        
    # 4. Si todo está perfecto, lo dejamos pasar
    return {"mensaje": "Login exitoso", "usuario": usuario}

# --- EN TU ARCHIVO DE RUTAS DE USUARIOS ---

@router.put("/{usuario_id}")
def actualizar_usuario(usuario_id: int, usuario_actualizado: dict, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Actualizamos los campos que nos manden
    if "nombre_completo" in usuario_actualizado: 
        usuario.nombre_completo = usuario_actualizado["nombre_completo"]
    if "username" in usuario_actualizado: 
        usuario.username = usuario_actualizado["username"]
    if "rol" in usuario_actualizado: 
        usuario.rol = usuario_actualizado["rol"]
    if "sucursal_id" in usuario_actualizado: 
        usuario.sucursal_id = usuario_actualizado["sucursal_id"]
        
    # --- AQUÍ ESTÁ LA CORRECCIÓN ---
    # Si viene una contraseña nueva y no está vacía, la encriptamos antes de guardarla
    if "password" in usuario_actualizado and usuario_actualizado["password"]: 
        salt = bcrypt.gensalt()
        hashed_password_bytes = bcrypt.hashpw(usuario_actualizado["password"].encode('utf-8'), salt)
        # Ojo aquí: Lo guardamos en 'hashed_password', no en 'password'
        usuario.hashed_password = hashed_password_bytes.decode('utf-8')
    
    db.commit()
    return {"mensaje": "Usuario actualizado"}

@router.delete("/{usuario_id}")
def eliminar_usuario(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(usuario)
    db.commit()
    return {"mensaje": "Usuario eliminado"}