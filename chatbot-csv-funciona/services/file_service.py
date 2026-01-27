import os
import logging
import pandas as pd
from fastapi import UploadFile
from typing import Tuple
from config import settings

logger = logging.getLogger(__name__)

class FileService:
    """Servicio para operaciones con archivos"""
    
    @staticmethod
    async def save_upload_file(file: UploadFile) -> str:
        """Guarda un archivo subido y devuelve su ruta"""
        file_path = os.path.join(settings["uploads_dir"], file.filename)
        
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
            
        return file_path
    
    @staticmethod
    def process_file(file_path: str) -> Tuple[pd.DataFrame, str]:
        """Procesa un archivo y devuelve un DataFrame y ruta procesada"""
        filename = os.path.basename(file_path)
        extension = filename.split('.')[-1].lower()
        
        # Cargar según el tipo de archivo
        if extension in ['xlsx', 'xls']:
            df = pd.read_excel(file_path)
            processed_path = os.path.join(
                settings["processed_dir"], 
                f"{os.path.splitext(filename)[0]}.csv"
            )
            df.to_csv(processed_path, index=False)
        elif extension == 'csv':
            df = pd.read_csv(file_path)
            processed_path = file_path
        else:
            raise ValueError(f"Formato de archivo no soportado: {extension}")
            
        return df, processed_path