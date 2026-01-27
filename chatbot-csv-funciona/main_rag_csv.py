from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from openai import AsyncOpenAI
from websockets.exceptions import ConnectionClosed

import chromadb
import json
import uvicorn
import logging
import pandas as pd
from datetime import datetime
import os
from typing import List, Dict, Any

# Configuración de logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuraciones
ENDPOINT = "http://cortex_csv:39281/v1"
MODEL = "llama3.2:1b"
CSV_PATH = "data/facturas.csv"
COLLECTION_NAME = "facturas_enhanced"
USE_SIMPLE_MODE = False  # Cambiar a True para usar el modo simple

# Cliente OpenAI (adaptado a servidor local de Cortex)
ai_client = AsyncOpenAI(
    base_url=ENDPOINT,
    api_key="not-needed"
)
    

# Sistema RAG simple
def setup_simple_rag():
    """Configura el sistema RAG simple con documentos predefinidos"""
    client = chromadb.Client()
    
    # Eliminar colección si existe
    try:
        client.delete_collection("all-my-documents")
    except:
        pass
    
    # Crear colección con documentos estáticos
    collection = client.create_collection("all-my-documents")
    logger.info(f"Colección {collection} eliminada")
    print('collection',collection)
    collection.add(
        documents=[
            "La empresa Lostsys se dedica a ofrecer servícios y productos a empresas sobre informática corporativa como software de gestión, CRMs, ERPs, portales corporativos, eCommerce, formación, DevOps, etc.",
            "En Lostsys podemos ayudarte ha mejorar tus procesos de CI/CD con nuestros productos y servícios de DevOps.",
            "En Lostsys podemos ayudarte a digitalizarte con nuestros servícios de desarrollo de aplicaciones corporativas.",
            "En Lostsys te podemos entrenar y formar a múltiples áreas de la informática corporativa como desarrollo, Data, IA o DevOps.",
            "En Lostsys te podemos desarrollar una tienda online para vender por todo el mundo y mas allà.",
            "En Lostsys te podemos desarrollar un eCommerce para vender por todo el mundo y mas allà",
        ],
        ids=["id1", "id2", "id3", "id4", "id5", "id6"]
    )
    
    return client, collection

# Prompt del sistema simple
simple_system_prompt = """
Eres un asistente de la empresa Lostsys que ayuda a sus clientes a encontrar el servicio o producto que les interesa. Sigue estas instrucciones:
- Ofrece respuestas cortas y concisas de no mas de 25 palabras. 
- No ofrezcas consejos, productos o servícios de terceros.
- Explica al cliente cosas relacionadas con en la siguiente lista JSON: 
"""

class EnhancedRAGSystem:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.chroma_client = chromadb.Client()

        logger.info(f"que tiene {self.chroma_client} chroma")
        self._setup_collection()
        logger.info(f"que tiene {self._setup_collection()} coleccion")
        
    def _process_data(self, df: pd.DataFrame):
        """Procesa y limpia el DataFrame para mejorar la calidad de los datos"""
        try:
            # Convertir tipos de datos
            df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
            df["importe"] = pd.to_numeric(df["importe"], errors="coerce")
            
            # Filtrar filas inválidas
            df = df.dropna(subset=["fecha", "importe", "cliente", "pais"])
            
            # Añadir información derivada
            df["mes"] = df["fecha"].dt.month
            df["año"] = df["fecha"].dt.year
            
            return df
        except Exception as e:
            logger.error(f"Error procesando datos: {str(e)}")
            return df
        
    def _create_documents(self, df: pd.DataFrame):
        """Crea documentos enriquecidos con información detallada de las facturas"""
        documents = []
        metadatas = []
        ids = []
        
        # Documentos de facturas individuales
        for idx, row in df.iterrows():
            document = (
                f"Factura {idx}: El día {row['fecha'].strftime('%d/%m/%Y')}, "
                f"el cliente {row['cliente']} de {row['pais']} "
                f"generó un importe de {row['importe']:.2f}."
            )
            metadata = {
                "tipo": "factura",
                "cliente": row["cliente"],
                "pais": row["pais"],
                "fecha": row["fecha"].strftime("%Y-%m-%d"),
                "importe": float(row["importe"]),
                "mes": int(row["mes"]),
                "año": int(row["año"])
            }
            documents.append(document)
            metadatas.append(metadata)
            ids.append(f"factura_{idx}")
        
        # Crear resúmenes estadísticos
        if len(df) > 0:
            # Resumen general
            general_stats = (
                f"Resumen general de facturas:\n"
                f"Total de facturas: {len(df)}\n"
                f"Importe total: {df['importe'].sum():.2f}\n"
                f"Importe promedio: {df['importe'].mean():.2f}\n"
                f"Importe mínimo: {df['importe'].min():.2f}\n"
                f"Importe máximo: {df['importe'].max():.2f}\n"
                f"Periodo: {df['fecha'].min().strftime('%d/%m/%Y')} a {df['fecha'].max().strftime('%d/%m/%Y')}\n"
                
                f"Número de clientes únicos: {df['cliente'].nunique()}\n"
                f"Número de países: {df['pais'].nunique()}"
            )
            documents.append(general_stats)
            metadatas.append({"tipo": "estadistica", "subtipo": "general"})
            ids.append("stats_general")
            
            # Top clientes
            clientes_stats = "Estadísticas por cliente:\n"
            top_clientes = df.groupby("cliente")["importe"].sum().sort_values(ascending=False).head(5)
            for cliente, importe in top_clientes.items():
                clientes_stats += f"- {cliente}: {importe:.2f}\n"
            documents.append(clientes_stats)
            metadatas.append({"tipo": "estadistica", "subtipo": "clientes"})
            ids.append("stats_clientes")
            
            # Top países
            paises_stats = "Estadísticas por país:\n"
            top_paises = df.groupby("pais")["importe"].sum().sort_values(ascending=False).head(5)
            for pais, importe in top_paises.items():
                paises_stats += f"- {pais}: {importe:.2f}\n"
            documents.append(paises_stats)
            metadatas.append({"tipo": "estadistica", "subtipo": "paises"})
            ids.append("stats_paises")
            
            # Estadísticas por mes
            meses_stats = "Estadísticas por mes:\n"
            meses_df = df.groupby(df["fecha"].dt.month)["importe"].sum().sort_values(ascending=False)
            meses_nombres = {
                1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
                7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
            }
            for mes, importe in meses_df.items():
                meses_stats += f"- {meses_nombres.get(mes, str(mes))}: {importe:.2f}\n"
            documents.append(meses_stats)
            metadatas.append({"tipo": "estadistica", "subtipo": "meses"})
            ids.append("stats_meses")
        
        return documents, metadatas, ids
        
    def _setup_collection(self):
        """Configura la colección de ChromaDB y carga los datos"""
        try:
            # Eliminar colección si existe
            try:
                self.chroma_client.delete_collection(COLLECTION_NAME)
                logger.info(f"Colección anterior {COLLECTION_NAME} eliminada")
            except:
                pass
            
            # Crear nueva colección
            self.collection = self.chroma_client.create_collection(
                name=COLLECTION_NAME
            )
            
            # Cargar y procesar datos
            logger.info(f"Cargando datos desde {self.csv_path}")
            df = pd.read_csv(self.csv_path)
            
            # Verificar columnas necesarias
            required_columns = ["fecha", "cliente", "pais", "importe"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Faltan columnas requeridas: {missing_columns}")
            
            # Procesar datos
            df_processed = self._process_data(df)
            logger.info(f"Datos procesados: {len(df_processed)} registros válidos")
            
            # Crear documentos
            documents, metadatas, ids = self._create_documents(df_processed)
            
            # Añadir documentos a ChromaDB
            batch_size = 50  # Procesar en lotes para evitar problemas de memoria
            for i in range(0, len(documents), batch_size):
                end_idx = min(i + batch_size, len(documents))
                self.collection.add(
                    documents=documents[i:end_idx],
                    metadatas=metadatas[i:end_idx],
                    ids=ids[i:end_idx]
                )
            
            logger.info(f"Datos cargados en ChromaDB: {len(documents)} documentos")
            logger.info(f"Datos coleccion: {(self.collection)} documentos")
            
        except Exception as e:
            logger.error(f"Error configurando la colección: {str(e)}")
            # Crear colección de respaldo con mensaje de error
            self.collection = self.chroma_client.create_collection(name=COLLECTION_NAME)
            self.collection.add(
                documents=["Error cargando datos de facturas: " + str(e)],
                ids=["error_1"]
            )
    
    async def query(self, user_query: str, k: int = 6) -> Dict[str, Any]:
        """Realiza una consulta y recupera documentos relevantes"""
        try:
            # Consultar ChromaDB
            results = self.collection.query(
                query_texts=[user_query],
                n_results=k
            )
            
            # Obtener documentos e ids
            documents = results["documents"][0]
            
            # Agregar estadísticas generales para consultas de resumen
            if any(palabra in user_query.lower() for palabra in ["total", "resumen", "estadística", "general"]):
                # Buscar documentos de estadísticas
                stats_results = self.collection.query(
                    query_texts=["estadísticas resumen general"],
                    where={"tipo": "estadistica"},
                    n_results=4
                )
                # Añadir al contexto si no están ya incluidos
                for doc in stats_results["documents"][0]:
                    if doc not in documents:
                        documents.append(doc)
            
            # Construir contexto completo
            context = "\n\n".join(documents)
            
            return {
                "context": context,
                "has_relevant_info": len(documents) > 0
            }
            
        except Exception as e:
            logger.error(f"Error consultando ChromaDB: {str(e)}")
            return {
                "context": f"Error recuperando información: {str(e)}",
                "has_relevant_info": False
            }

# Inicializar sistema según el modo seleccionado
if USE_SIMPLE_MODE:
    logger.info("Inicializando en modo simple")
    simple_client, simple_collection = setup_simple_rag()
    rag_system = None
else:
    logger.info("Inicializando en modo avanzado")
    rag_system = EnhancedRAGSystem(csv_path=CSV_PATH)
    simple_client = None
    simple_collection = None

# Aplicación FastAPI
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return RedirectResponse("/static/index.html")

# Endpoint /api/templates eliminado conforme a la solicitud

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
        logging.info("Conexión cerrada")
    except Exception as e:
        logging.error(f"Error en websocket: {str(e)}")
        try:
            await websocket.send_json({
                "action": "error",
                "content": f"Error en la conexión: {str(e)}"
            })
        except:
            pass

async def process_messages(messages, websocket):
    if USE_SIMPLE_MODE:
        # Modo simple (empresa Lostsys)
        user_query = messages[-1]["content"]
        
        # Consulta a ChromaDB
        results = simple_collection.query(
            query_texts=[user_query],
            n_results=2
        )
        
        # Crear mensaje del sistema
        pmsg = [{"role": "system", "content": simple_system_prompt + str(results["documents"][0])}]
        completion_payload = {
            "messages": pmsg + messages
        }
        
        # Solicitud al modelo
        response = await ai_client.chat.completions.create(
            top_p=0.9,
            temperature=0.6,
            model=MODEL,
            messages=completion_payload["messages"],
            stream=True
        )
    else:
        # Modo avanzado (análisis de facturas)
        user_query = messages[-1]["content"]
        
        # Consultar RAG
        rag_result = await rag_system.query(user_query)
        
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
        {rag_result["context"]}
        [FIN CONTEXTO]
        
        [PREGUNTA]
        {user_query}
        [FIN PREGUNTA]
        """
        
        # Crear mensaje para el modelo
        completion_messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Solicitar respuesta al modelo
        response = await ai_client.chat.completions.create(
            model=MODEL,
            messages=completion_messages,
            temperature=0.1,
            top_p=0.9,
            max_tokens=512,
            stream=True
        )
    
    # Streaming hacia el frontend (común para ambos modos)
    async for chunk in response:
        if (not chunk.choices[0] or
            not chunk.choices[0].delta or
            not chunk.choices[0].delta.content):
            continue

        await websocket.send_json({
            "action": "append_system_response",
            "content": chunk.choices[0].delta.content
        })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)