from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

# Importamos nuestros archivos de la carpeta principal
import models, schemas
from database import get_db

# Configuramos el router para agrupar todas las rutas de sucursales
router = APIRouter(
    prefix="/sucursales",
    tags=["Sucursales"]
)

# Ruta 1: POST para CREAR una sucursal nueva
@router.post("/", response_model=schemas.Sucursal)
def crear_sucursal(sucursal: schemas.SucursalCreate, db: Session = Depends(get_db)):
    # 1. Verificamos que no exista otra sucursal con el mismo nombre para evitar duplicados
    db_sucursal = db.query(models.Sucursal).filter(models.Sucursal.nombre == sucursal.nombre).first()
    if db_sucursal:
        raise HTTPException(status_code=400, detail="Ya existe una sucursal con este nombre")
    
    # 2. Preparamos los datos para guardarlos usando nuestro modelo
    nueva_sucursal = models.Sucursal(
        nombre=sucursal.nombre,
        direccion=sucursal.direccion,
        telefono=sucursal.telefono,
        tiene_produccion=sucursal.tiene_produccion # <-- ¡YA NO SE PIERDE EL DATO AL CREAR!
    )
    
    # 3. Guardamos en la base de datos
    db.add(nueva_sucursal)
    db.commit()
    db.refresh(nueva_sucursal) # Actualizamos para obtener el ID que le asignó Postgres
    
    return nueva_sucursal

# Ruta 2: GET para OBTENER todas las sucursales
@router.get("/", response_model=List[schemas.Sucursal])
def obtener_sucursales(db: Session = Depends(get_db)):
    sucursales = db.query(models.Sucursal).all()
    return sucursales

# Ruta 3: PUT para ACTUALIZAR una sucursal existente (¡CORREGIDA!)
@router.put("/{sucursal_id}", response_model=schemas.Sucursal)
def actualizar_sucursal(sucursal_id: int, sucursal_actualizada: schemas.SucursalCreate, db: Session = Depends(get_db)):
    sucursal = db.query(models.Sucursal).filter(models.Sucursal.id == sucursal_id).first()
    if not sucursal:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    
    # Asignamos TODOS los valores que manda React a la base de datos
    sucursal.nombre = sucursal_actualizada.nombre
    sucursal.direccion = sucursal_actualizada.direccion # (Ya no dice "ubicacion")
    sucursal.telefono = sucursal_actualizada.telefono
    sucursal.tiene_produccion = sucursal_actualizada.tiene_produccion # <-- ¡LA CLAVE DEL ÉXITO!
    
    db.commit()
    db.refresh(sucursal)
    return sucursal

# Ruta 4: DELETE para BORRAR una sucursal
@router.delete("/{sucursal_id}")
def eliminar_sucursal(sucursal_id: int, db: Session = Depends(get_db)):
    sucursal = db.query(models.Sucursal).filter(models.Sucursal.id == sucursal_id).first()
    if not sucursal:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    
    db.delete(sucursal)
    db.commit()
    return {"mensaje": "Sucursal eliminada"}