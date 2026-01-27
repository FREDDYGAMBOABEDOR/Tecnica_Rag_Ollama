from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from websockets.exceptions import ConnectionClosed
import uvicorn
import logging
import os

# Importar servicios y módulos
from services.llm_service import LLMService
from rag.retriever import RAGRetriever
from config import settings

# Configuración de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear directorios necesarios
os.makedirs("data/uploads", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)

# Inicializar servicios
llm_service = LLMService()
rag_retriever = RAGRetriever()

# Inicializar colección con datos predeterminados
try:
    rag_retriever.initialize_collection("data/facturas.csv")
except Exception as e:
    logger.error(f"Error inicializando colección: {str(e)}")





# Aplicación FastAPI
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return RedirectResponse("/static/index.html")

@app.websocket("/init")
async def init(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            await websocket.send_json({"action": "init_system_response"})
            await process_messages(data, websocket)
            await websocket.send_json({"action": "finish_system_response"})
    except (WebSocketDisconnect, ConnectionClosed):
        logger.info("Conexión cerrada")

async def process_messages(messages, websocket):
    # Obtener consulta del usuario
    user_query = messages[-1]["content"]
    
    # Consultar RAG para obtener contexto
    rag_result = await rag_retriever.query(user_query)
    
    # Generar respuesta con LLM
    await llm_service.generate_response(
        context=rag_result["context"],
        query=user_query,
        websocket=websocket
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)