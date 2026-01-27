# Excel RAG Analyzer con Plantillas

Este sistema permite analizar archivos Excel de diferentes estructuras utilizando plantillas configurables y generar respuestas a consultas a través de un sistema RAG (Retrieval-Augmented Generation).

## Características

- **Plantillas configurables**: Permite definir diferentes estructuras de Excel para adaptarse a diversos formatos
- **Detección automática**: Sugiere plantillas basadas en la estructura del archivo
- **Soporte para diversas estructuras**: Compatible con datos horizontales, diferentes encabezados y formatos
- **Sistema RAG integrado**: Utiliza ChromaDB para indexar los datos y generar respuestas contextuales
- **Compatible con Ollama**: Utiliza modelos de Ollama para generar respuestas en lenguaje natural

## Estructura del Proyecto

```
chatbot-csv/
├── main.py                      # Archivo principal
├── config.py                    # Configuraciones y plantillas predeterminadas
├── rag/                         # Sistema RAG
│   ├── __init__.py
│   ├── embeddings.py            # Manejo de embeddings
│   ├── retriever.py             # Recuperación de documentos (adaptado para plantillas)
│   └── processor.py             # Procesamiento de documentos (adaptado para plantillas)
├── services/                    # Servicios
│   ├── __init__.py
│   ├── file_service.py          # Manejo de archivos (adaptado para plantillas)
│   ├── llm_service.py           # Servicio de LLM (adaptado para plantillas)
│   └── excel_template_service.py # Nuevo servicio para gestionar plantillas
├── api/                         # API y endpoints
│   ├── __init__.py
│   ├── routes.py                # Rutas HTTP (con nuevos endpoints para plantillas)
│   └── websocket.py             # Manejo de WebSockets (adaptado para plantillas)
├── data/                        # Datos
│   ├── uploads/                 # Archivos subidos
│   └── processed/               # Archivos procesados
├── static/                      # Estáticos
│   ├── index.html               # Nueva interfaz con selección de plantillas
│   ├── css/app.css              # Estilos
│   └── js/app.js                # JavaScript para la interfaz
├── config/                      # Directorio para configuraciones
│   └── templates.json           # Plantillas de Excel guardadas
└── utils/                       # Utilidades
    ├── __init__.py
    └── helpers.py               # Funciones de ayuda
```

## Plantillas Predefinidas

El sistema incluye tres plantillas predefinidas:

1. **Ventas Diarias**: Para reportes de ventas diarias con estructura horizontal
   - Columnas clave: Local, fecha
   - Columnas de valor: Base0, Base<>0, Impuestos, Venta-Impuesto, Suma de total_venta_sinimpuestos

2. **Inventario**: Para reportes de inventario y stock de productos
   - Columnas clave: Codigo, Producto
   - Columnas de valor: Stock, Costo, Precio, Ubicacion

3. **Facturas**: Para registros de facturas y transacciones
   - Columnas clave: fecha, cliente
   - Columnas de valor: importe, pais

## Instalación y Ejecución

1. **Requisitos previos**:
   - Python 3.8 o superior
   - Ollama instalado y funcionando

2. **Instalar dependencias**:
   ```bash
   pip install fastapi uvicorn pandas chromadb openai
   ```

3. **Ejecutar la aplicación**:
   ```bash
   python main.py
   ```

4. **Acceder a la interfaz**:
   Abrir en el navegador: `http://localhost:8000`

## Uso

1. **Seleccionar Plantilla**: En la pantalla inicial, elige la plantilla que mejor se adapte a la estructura de tu Excel.

2. **Cargar Archivo**: Sube un archivo Excel (.xlsx, .xls) o CSV (.csv) con la estructura correspondiente a la plantilla.

3. **Analizar Datos**: Haz clic en "Analizar Excel" para procesar el archivo con la plantilla seleccionada.

4. **Realizar Consultas**: Una vez procesado, podrás hacer preguntas en lenguaje natural sobre los datos.

## Ejemplos de Consultas

Dependiendo de la plantilla seleccionada, puedes hacer diferentes tipos de consultas:

### Plantilla Ventas Diarias:
- "¿Cuál fue el total de ventas para el local 002-GUASMO?"
- "¿Qué día tuvo la mayor venta en marzo?"
- "¿Cuál es el promedio de impuestos recaudados?"

### Plantilla Inventario:
- "¿Cuántos productos tienen stock menor a 10 unidades?"
- "¿Cuál es el valor total del inventario a precio de venta?"
- "¿Qué productos están ubicados en la bodega principal?"

### Plantilla Facturas:
- "¿Cuál es el cliente con mayor importe total?"
- "¿Cuántas facturas se emitieron para clientes de España?"
- "¿Cuál fue el mes con mayor facturación?"

## Personalización

### Crear Nuevas Plantillas

Puedes crear nuevas plantillas a través de la API:

```python
import requests

template = {
    "name": "Mi Plantilla",
    "description": "Descripción de la plantilla",
    "header_row": 0,
    "data_start_row": 1,
    "key_columns": ["IDPrimario", "Nombre"],
    "value_columns": ["Valor1", "Valor2"],
    "column_mappings": {
        "id": "IDPrimario",
        "nombre": "Nombre",
        "valor": "Valor1"
    },
    "skip_empty_rows": True,
    "horizontal_data": True
}

response = requests.post("http://localhost:8000/api/templates", json=template)
print(response.json())
```

## Configuración

La configuración principal se encuentra en `config.py`. Puedes modificar:

- **Directorios**: Rutas para archivos subidos y procesados
- **Endpoints**: Configuración para Ollama
- **Modelo**: Modelo a utilizar con Ollama
- **Plantillas Predeterminadas**: Definiciones de plantillas que se cargan inicialmente

## Desarrollo

Para añadir soporte para nuevos tipos de plantillas:

1. Modifica `rag/processor.py` para añadir un nuevo método específico de procesamiento
2. Actualiza `services/excel_template_service.py` si es necesario añadir nuevas funcionalidades
3. Agrega un prompt específico en `services/llm_service.py` para la nueva plantilla

## Solución de Problemas

- **Error al cargar archivo**: Verifica que el archivo tenga la estructura esperada por la plantilla
- **Respuestas imprecisas**: Asegúrate de que la plantilla seleccionada coincida con la estructura del Excel
- **Error de conexión con Ollama**: Verifica que Ollama esté funcionando correctamente