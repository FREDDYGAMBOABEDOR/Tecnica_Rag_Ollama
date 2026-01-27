from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from websockets.exceptions import ConnectionClosed
import logging
from services.llm_service import LLMService
from rag.retriever import RAGRetriever

router = APIRouter()
logger = logging.getLogger(__name__)

# Servicios
llm_service = LLMService()
rag_retriever = RAGRetriever()

@router.websocket("/init")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Recibir mensaje
            data = await websocket.receive_json()
            
            # Iniciar respuesta
            await websocket.send_json({"action": "init_system_response"})
            
            # Obtener consulta del usuario
            user_query = data[-1]["content"]
            
            # Consultar RAG para obtener contexto
            rag_result = await rag_retriever.query(user_query)
            
            # Generar respuesta con LLM
            await llm_service.generate_response(
                context=rag_result["context"],
                query=user_query,
                websocket=websocket
            )
            
            # Finalizar respuesta
            await websocket.send_json({"action": "finish_system_response"})
            
    except WebSocketDisconnect:
        logger.info("WebSocket desconectado")
    except ConnectionClosed:
        logger.info("Conexión cerrada")
    except Exception as e:
        logger.error(f"Error en WebSocket: {str(e)}")
        try:
            await websocket.send_json({
                "action": "error",
                "content": f"Error: {str(e)}"
            })
        except:
            pass