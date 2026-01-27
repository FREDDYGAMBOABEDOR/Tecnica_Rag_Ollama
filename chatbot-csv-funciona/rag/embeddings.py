import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        """El servicio de embeddings usa por defecto el embebedor interno de ChromaDB"""
        logger.info("Usando modelo de embeddings por defecto de ChromaDB")
        self.use_custom_model = False
        
    def get_embedding_function(self):
        """Devuelve la función de embedding para usar con ChromaDB"""
        # Devuelve None para usar el embebedor predeterminado de ChromaDB
        return None