import os
import logging
from config import settings

logger = logging.getLogger(__name__)

def create_required_directories():
    """Crea los directorios necesarios para la aplicación"""
    try:
        os.makedirs(settings["uploads_dir"], exist_ok=True)
        os.makedirs(settings["processed_dir"], exist_ok=True)
        logger.info("Directorios creados correctamente")
    except Exception as e:
        logger.error(f"Error creando directorios: {str(e)}")

def format_file_size(size_bytes):
    """Formatea el tamaño de un archivo en bytes a una forma legible"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"