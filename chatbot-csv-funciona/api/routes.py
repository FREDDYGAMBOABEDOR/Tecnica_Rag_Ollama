from fastapi import APIRouter, UploadFile, File, Form  # Añadido Form
from fastapi.responses import HTMLResponse, JSONResponse
import os
import json  # Añadido json para process-mapped-file
import logging
from services.file_service import FileService
from rag.retriever import RAGRetriever
from config import settings  # Añadido settings que faltaba

router = APIRouter()
logger = logging.getLogger(__name__)

# Servicios
file_service = FileService()
rag_retriever = RAGRetriever()

@router.get("/", response_class=HTMLResponse)
async def root():
    """Ruta principal que sirve la página HTML"""
    with open("static/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Endpoint para subir archivos"""
    try:
        # Verificar extensión de archivo
        filename = file.filename
        extension = filename.split('.')[-1].lower()
        if extension not in ['csv', 'xlsx', 'xls']:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Tipo de archivo no permitido"}
            )
        
        # Guardar archivo
        file_path = await file_service.save_upload_file(file)
        
        # Procesar archivo
        df, processed_path = file_service.process_file(file_path)
        
        # Inicializar colección RAG
        rag_retriever.initialize_collection(processed_path)
        
        return JSONResponse(content={
            "status": "success",
            "message": "Archivo cargado correctamente",
            "file_path": processed_path,
            "rows": len(df),
            "columns": list(df.columns)
        })
        
    except Exception as e:
        logger.error(f"Error cargando archivo: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@router.post("/analyze-file")
async def analyze_file(file: UploadFile = File(...)):
    """Analiza el archivo y sugiere mapeos de columnas"""
    try:
        # Guardar archivo temporalmente
        file_path = await file_service.save_upload_file(file)
        df, _ = file_service.process_file(file_path)
        
        # Obtener columnas del archivo
        columns = list(df.columns)
        
        # Analizar columnas y sugerir mapeos
        suggested_mappings = {}
        
        # Detectar posibles columnas de fecha
        date_cols = [col for col in columns if any(
            keyword in col.lower() for keyword in ["fecha", "date", "dia", "day", "time"]
        )]
        if date_cols:
            suggested_mappings["fecha"] = date_cols[0]
            
        # Detectar posibles columnas de cliente
        client_cols = [col for col in columns if any(
            keyword in col.lower() for keyword in ["cliente", "client", "customer", "nombre", "name"]
        )]
        if client_cols:
            suggested_mappings["cliente"] = client_cols[0]
            
        # Detectar posibles columnas de país
        country_cols = [col for col in columns if any(
            keyword in col.lower() for keyword in ["pais", "country", "nacion", "location"]
        )]
        if country_cols:
            suggested_mappings["pais"] = country_cols[0]
            
        # Detectar posibles columnas de importe
        amount_cols = [col for col in columns if any(
            keyword in col.lower() for keyword in ["importe", "amount", "valor", "precio", "price", "total"]
        )]
        if amount_cols:
            suggested_mappings["importe"] = amount_cols[0]
        
        # Extraer una muestra pequeña para vista previa
        preview_data = df.head(5).to_dict('records')
        
        return JSONResponse(content={
            "status": "success",
            "columns": columns,
            "suggested_mappings": suggested_mappings,
            "preview_data": preview_data,
            "file_path": file_path
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@router.post("/process-mapped-file")
async def process_mapped_file(file_path: str = Form(...), mappings: str = Form(...)):
    """Procesa el archivo con los mapeos definidos por el usuario"""
    try:
        mappings_dict = json.loads(mappings)
        
        # Cargar archivo
        df, _ = file_service.process_file(file_path)
        
        # Crear nuevo DataFrame con columnas renombradas según mapeo
        df_mapped = pd.DataFrame()
        for system_col, file_col in mappings_dict.items():
            if file_col in df.columns:
                df_mapped[system_col] = df[file_col]
        
        # Verificar columnas requeridas
        required_columns = ["fecha", "cliente", "pais", "importe"]
        missing_columns = [col for col in required_columns if col not in df_mapped.columns]
        if missing_columns:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error", 
                    "message": f"Faltan columnas requeridas: {', '.join(missing_columns)}"
                }
            )
        
        # Guardar versión mapeada
        mapped_filename = f"mapped_{os.path.basename(file_path)}"
        processed_path = os.path.join(settings["processed_dir"], mapped_filename)
        df_mapped.to_csv(processed_path, index=False)
        
        # Inicializar colección RAG
        rag_retriever.initialize_collection(processed_path)
        
        return JSONResponse(content={
            "status": "success",
            "message": "Archivo procesado correctamente con mapeo personalizado",
            "rows": len(df_mapped),
            "columns": list(df_mapped.columns)
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

# Añadido: Endpoint para templates que faltaba
@router.get("/api/templates")
async def get_templates():
    """Proporciona plantillas de preguntas predefinidas para la interfaz"""
    templates = [
        {
            "id": "resumen_general",
            "title": "Resumen General",
            "prompt": "Dame un resumen general de las ventas de todos los locales"
        },
        {
            "id": "local_especifico",
            "title": "Analizar Local",
            "prompt": "¿Cuál fue el rendimiento del local GUASMO durante marzo?"
        },
        {
            "id": "comparar_locales",
            "title": "Comparar Locales",
            "prompt": "Compara las ventas entre GUASMO y PENDOLA en abril"
        },
        {
            "id": "mejores_dias",
            "title": "Mejores Días",
            "prompt": "¿Cuáles fueron los 5 días con mayores ventas?"
        },
        {
            "id": "estadisticas_impuestos",
            "title": "Estadísticas de Impuestos",
            "prompt": "¿Qué local generó más impuestos y en qué fecha?"
        },
        {
            "id": "tendencias",
            "title": "Tendencias de Ventas",
            "prompt": "Muestra la tendencia de ventas en mayo para todos los locales"
        }
    ]
    
    return JSONResponse(content=templates)