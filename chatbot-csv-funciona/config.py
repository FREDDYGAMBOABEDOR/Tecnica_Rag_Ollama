import os

# Configuración del servicio
ENDPOINT = os.getenv("LLM_ENDPOINT", "http://cortex_csv:39281/v1")
MODEL = os.getenv("LLM_MODEL", "llama3.2:1b")
API_KEY = "not-needed"

# Configuración de ChromaDB
COLLECTION_NAME = "facturas_enhanced"

# Rutas de datos
DATA_DIR = "data"
UPLOADS_DIR = f"{DATA_DIR}/uploads"
PROCESSED_DIR = f"{DATA_DIR}/processed"
DEFAULT_CSV = f"{DATA_DIR}/facturas.csv"

# Configuración global disponible para importar
settings = {
    "endpoint": ENDPOINT,
    "model": MODEL,
    "api_key": API_KEY,
    "collection_name": COLLECTION_NAME,
    "uploads_dir": UPLOADS_DIR,
    "processed_dir": PROCESSED_DIR,
    "default_csv": DEFAULT_CSV
}