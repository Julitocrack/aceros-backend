import os
import json
import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List
from dotenv import load_dotenv
from datetime import datetime
import google.generativeai as genai # <-- NUEVA LIBRERÍA VIP
from PIL import Image
import io

import models, schemas
from database import get_db

load_dotenv()
cloudinary.config(secure=True)

# Configuración de la Inteligencia Artificial
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# Usamos el modelo Flash que es rapidísimo y muy barato/gratis
modelo_ia = genai.GenerativeModel('gemini-2.5-flash') 

router = APIRouter(
    prefix="/pedidos",
    tags=["Pedidos"]
)

# --- NUEVA RUTA VIP: ANALIZAR TICKET CON IA ---
@router.post("/analizar-ticket")
async def analizar_ticket(foto: UploadFile = File(...)):
    try:
        # Leemos la imagen en memoria para pasársela a la IA
        contents = await foto.read()
        # ¡CORRECCIÓN AQUÍ! (Era io.BytesIO, no io.BytesBytesIO)
        img = Image.open(io.BytesIO(contents)) 
        
        # Le damos instrucciones precisas a la IA
        prompt = """
        Eres un experto extrayendo datos de tickets de compra de ferreterías.
        Analiza esta imagen y devuélveme ÚNICAMENTE un objeto JSON válido con 2 campos:
        1. "numero_ticket": El número de ticket, folio o factura (solo números y letras, sin la palabra ticket). Si no hay, pon "".
        2. "detalles": Una lista limpia del material comprado (cantidad y descripción). Ignora precios, totales, fechas y datos de la tienda.
        Ejemplo de salida exacta: {"numero_ticket": "12939", "detalles": "141 KILOS DEL R01/6 LAM ZINTRO\n10 PIJAS"}
        """
        
        respuesta = modelo_ia.generate_content([prompt, img])
        texto_limpio = respuesta.text.replace('```json', '').replace('```', '').strip()
        datos_extraidos = json.loads(texto_limpio)
        
        # Regresamos el puntero del archivo a 0 por si Cloudinary lo necesita después
        await foto.seek(0) 
        return datos_extraidos
        
    except Exception as e:
        print(f"Error de IA: {e}") # Si falla algo, ahora lo verás en la terminal negra de Uvicorn
        # Si la IA falla, devolvemos vacío para no bloquear a la vendedora
        return {"numero_ticket": "", "detalles": ""}

@router.post("/leer-traspaso")
async def leer_traspaso(foto: UploadFile = File(...)):
    try:
        # Leemos la imagen en memoria para pasársela a la IA
        contents = await foto.read()
        img = Image.open(io.BytesIO(contents))
 
        # Le damos instrucciones precisas a la IA — DIFERENTES a las del ticket
        prompt = """
        Eres un asistente que lee notas escritas a mano por la dueña de una empresa de aceros en México.
        Estas notas son para mover material entre sucursales (traspasos de inventario internos).
 
        Transcribe LITERALMENTE TODO el texto que veas en la imagen, sin omitir nada.
        Reglas:
        - Conserva las medidas exactas tal como aparecen (1/2", 3/4, 1.5", calibre 14, 3 metros, etc.).
        - Conserva las cantidades tal como están escritas (50 pzs, 3 hojas, 2 rollos, 1 ton, etc.).
        - Si hay listas, una línea por ítem.
        - Si una palabra o número es ilegible, escribe [ilegible] en su lugar. NO inventes datos.
        - NO agregues encabezados, comentarios ni explicaciones de tu parte.
        - Devuelve SOLO el contenido de la nota, sin preámbulos.
 
        Si la imagen no contiene texto legible, responde EXACTAMENTE: NO_TEXTO_LEGIBLE
        """
 
        respuesta = modelo_ia.generate_content([prompt, img])
        texto = respuesta.text.strip()
 
        # Regresamos el puntero del archivo a 0 por si acaso
        await foto.seek(0)
 
        # Si la IA dijo que no hay texto legible, devolvemos vacío
        if texto == "NO_TEXTO_LEGIBLE":
            return {"texto": ""}
 
        return {"texto": texto}
 
    except Exception as e:
        print(f"Error de IA traspaso: {e}")  # Lo verás en la terminal de Uvicorn / logs de Railway
        # Si la IA falla, devolvemos vacío para no bloquear a la dueña
        return {"texto": ""}

# 1. CREAR PEDIDO (Actualizado con numero_ticket)
@router.post("/", response_model=schemas.Pedido)
async def crear_pedido(
    sucursal_id: int = Form(...),
    creador_id: int = Form(...),
    notas: str = Form(...),
    foto: UploadFile = File(...),
    requiere_matriz: str = Form("false"),
    requiere_produccion: str = Form("false"),
    tipo_orden: str = Form("Venta"),          
    sucursal_destino_id: int = Form(None),    
    numero_ticket: str = Form(None), # <-- AHORA RECIBIMOS EL NÚMERO
    db: Session = Depends(get_db)
):
    try:
        resultado = cloudinary.uploader.upload(foto.file)
        url_segura = resultado.get("secure_url")

        es_matriz = requiere_matriz.lower() == "true"
        es_produccion = requiere_produccion.lower() == "true"
        
        if tipo_orden == "Traspaso":
            estado_inicial = "Aprobado"
            destino_id = sucursal_destino_id
            fecha_aprob = datetime.utcnow() 
        else:
            estado_inicial = "Pendiente" if es_matriz else "Aprobado"
            destino_id = None if es_matriz else sucursal_id
            fecha_aprob = None if es_matriz else datetime.utcnow()
            if not es_matriz:
                es_produccion = True

        nuevo_pedido = models.Pedido(
            url_foto_ticket=url_segura,
            notas=notas,
            sucursal_id=sucursal_id,
            creador_id=creador_id,
            estado=estado_inicial,
            requiere_produccion=es_produccion,
            sucursal_destino_id=destino_id,
            tipo_orden=tipo_orden,
            fecha_aprobacion=fecha_aprob,
            numero_ticket=numero_ticket # <-- LO GUARDAMOS EN BD
        )
        
        db.add(nuevo_pedido)
        db.commit()
        db.refresh(nuevo_pedido)
        
        return nuevo_pedido
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir la foto: {str(e)}")

# 2. TODOS: Obtener todos los pedidos
@router.get("/", response_model=List[schemas.Pedido])
def obtener_pedidos(db: Session = Depends(get_db)):
    pedidos = db.query(models.Pedido).order_by(models.Pedido.fecha_creacion.desc()).all()
    return pedidos

# 3. DUEÑA: Aprueba el pedido
@router.put("/{pedido_id}/aprobar", response_model=schemas.Pedido)
def aprobar_pedido(pedido_id: int, datos: schemas.PedidoAprobar, db: Session = Depends(get_db)):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    pedido.estado = datos.estado 
    pedido.sucursal_destino_id = datos.sucursal_destino_id
    
    if pedido.tipo_orden == "Venta":
        pedido.requiere_produccion = True
    else:
        pedido.requiere_produccion = datos.requiere_produccion
    
    if datos.estado == "Aprobado":
        pedido.fecha_aprobacion = datetime.utcnow()
    
    db.commit()
    db.refresh(pedido)
    return pedido

# 4. PRODUCCIÓN / LOGÍSTICA
@router.put("/{pedido_id}/estado", response_model=schemas.Pedido)
def actualizar_estado(pedido_id: int, datos: schemas.PedidoEstadoUpdate, db: Session = Depends(get_db)):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    estados_validos = ["Pendiente", "Aprobado", "En_Produccion", "En_Logistica", "Entregado", "Rechazado"]
    if datos.estado not in estados_validos:
        raise HTTPException(status_code=400, detail=f"Estado no válido. Usa uno de: {estados_validos}")

    pedido.estado = datos.estado
    db.commit()
    db.refresh(pedido)
    return pedido