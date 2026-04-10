import os
from fastapi import APIRouter, UploadFile, File, HTTPException
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

# Esto lee tu archivo .env para buscar tu CLOUDINARY_URL sin exponerla en el código
load_dotenv()

# Cloudinary se configura automáticamente con la variable que acaba de leer
cloudinary.config(secure=True)

router = APIRouter(
    prefix="/archivos",
    tags=["Archivos"]
)

@router.post("/subir-foto")
async def subir_foto(file: UploadFile = File(...)):
    # 1. Validamos que el empleado realmente esté subiendo una foto y no un PDF o un virus
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")

    try:
        # 2. Cloudinary hace el trabajo pesado y la sube a la nube
        resultado = cloudinary.uploader.upload(file.file)
        
        # 3. Nos regresa muchísima info, pero solo nos importa el link seguro (https)
        url_foto = resultado.get("secure_url")
        
        return {"url_foto_ticket": url_foto}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir imagen a la nube: {str(e)}")