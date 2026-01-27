import logging
from openai import AsyncOpenAI
from config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """Servicio para interactuar con modelos de lenguaje"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=settings["endpoint"],
            api_key=settings["api_key"]
        )
        self.model = settings["model"]
    
    async def generate_response(self, context: str, query: str, websocket):
        """Genera una respuesta utilizando el LLM y la envía por websocket"""
        try:
            # Crear prompt con instrucciones detalladas
            system_prompt = f"""
            [INSTRUCCIÓN]
            Eres un analista estadístico especializado en el análisis de transacciones históricas.
            
            Sigue estas reglas estrictamente:
            1. Responde ÚNICAMENTE usando la información del CONTEXTO proporcionado.
            2. Si la información no está en el CONTEXTO, responde "No dispongo de suficiente información para responder a esta consulta."
            3. No inventes datos, nombres, fechas o estadísticas que no estén explícitos en el CONTEXTO.
            4. Da respuestas cortas, precisas y directas.
            5. Si te preguntan por tendencias o análisis no presentes en el CONTEXTO, indica que no puedes realizar análisis que vayan más allá de los datos proporcionados.
            
            [CONTEXTO]
            {context}
            [FIN CONTEXTO]
            
            [PREGUNTA]
            {query}
            [FIN PREGUNTA]
            """
            
            # Crear mensaje para el modelo
            completion_messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Solicitar respuesta al modelo con parámetros optimizados
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=completion_messages,
                temperature=0.1,  # Bajo para reducir alucinaciones
                top_p=0.9,
                max_tokens=512,
                stream=True
            )
            
            # Streaming hacia el frontend
            async for chunk in response:
                if (not chunk.choices[0] or
                    not chunk.choices[0].delta or
                    not chunk.choices[0].delta.content):
                    continue
                
                await websocket.send_json({
                    "action": "append_system_response",
                    "content": chunk.choices[0].delta.content
                })
                
        except Exception as e:
            logger.error(f"Error generando respuesta: {str(e)}")
            await websocket.send_json({
                "action": "append_system_response",
                "content": f"Error: {str(e)}"
            })