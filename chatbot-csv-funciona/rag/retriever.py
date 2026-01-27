import chromadb
import logging
import pandas as pd
from typing import Dict, Any
from config import settings
from rag.processor import DataProcessor

logger = logging.getLogger(__name__)

class RAGRetriever:
    def __init__(self):
        self.chroma_client = chromadb.Client()
        self.collection_name = settings["collection_name"]
        self.processor = DataProcessor()
        
    def initialize_collection(self, csv_path: str) -> bool:
        """Configura la colección de ChromaDB a partir de un archivo CSV"""
        try:
            # Eliminar colección si existe
            try:
                self.chroma_client.delete_collection(self.collection_name)
                logger.info(f"Colección anterior {self.collection_name} eliminada")
            except:
                pass
            
            # Crear nueva colección
            collection = self.chroma_client.create_collection(name=self.collection_name)
            
            # Cargar y procesar datos
            logger.info(f"Cargando datos desde {csv_path}")
            df = pd.read_csv(csv_path)
            
            # Verificar columnas necesarias
            required_columns = ["fecha", "cliente", "pais", "importe"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Faltan columnas requeridas: {missing_columns}")
            
            # Procesar datos
            df_processed = self.processor.process_dataframe(df)
            logger.info(f"Datos procesados: {len(df_processed)} registros válidos")
            
            # Crear documentos
            documents, metadatas, ids = self.processor.create_documents(df_processed)
            
            # Añadir documentos a ChromaDB
            batch_size = 50  # Procesar en lotes para evitar problemas de memoria
            for i in range(0, len(documents), batch_size):
                end_idx = min(i + batch_size, len(documents))
                collection.add(
                    documents=documents[i:end_idx],
                    metadatas=metadatas[i:end_idx],
                    ids=ids[i:end_idx]
                )
            
            logger.info(f"Datos cargados en ChromaDB: {len(documents)} documentos")
            return True
            
        except Exception as e:
            logger.error(f"Error configurando la colección: {str(e)}")
            # Crear colección de respaldo con mensaje de error
            collection = self.chroma_client.create_collection(name=self.collection_name)
            collection.add(
                documents=["Error cargando datos de facturas: " + str(e)],
                ids=["error_1"]
            )
            return False
    
    async def query(self, user_query: str, k: int = 6) -> Dict[str, Any]:
        """Realiza una consulta y recupera documentos relevantes"""
        try:
            collection = self.chroma_client.get_collection(self.collection_name)
            
            # Consultar ChromaDB
            results = collection.query(
                query_texts=[user_query],
                n_results=k
            )
            
            # Obtener documentos e ids
            documents = results["documents"][0]
            
            # Agregar estadísticas generales para consultas de resumen
            if any(palabra in user_query.lower() for palabra in ["total", "resumen", "estadística", "general"]):
                # Buscar documentos de estadísticas
                try:
                    stats_results = collection.query(
                        query_texts=["estadísticas resumen general"],
                        where={"tipo": "estadistica"},
                        n_results=4
                    )
                    # Añadir al contexto si no están ya incluidos
                    for doc in stats_results["documents"][0]:
                        if doc not in documents:
                            documents.append(doc)
                except:
                    pass  # Si no se puede filtrar por tipo, continuar
            
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

# import chromadb
# import logging
# import pandas as pd
# import re
# import numpy as np
# from typing import Dict, Any, List, Tuple
# from config import settings

# logger = logging.getLogger(__name__)

# class DataProcessor:
#     """Clase para procesar los datos y crear documentos para ChromaDB"""
    
#     def convertir_moneda(self, valor):
#         """Convierte valores monetarios en formato español a float"""
#         if isinstance(valor, str) and '$' in valor:
#             # Eliminar el símbolo de moneda y espacios
#             valor = valor.replace('$', '').strip()
#             # Eliminar puntos (separadores de miles) y reemplazar coma por punto (decimal)
#             valor = valor.replace('.', '').replace(',', '.')
#             return float(valor)
#         elif isinstance(valor, str) and re.match(r'\d+[\.,]\d+', valor):
#             # Convertir valores numéricos con formato decimal
#             return float(valor.replace(',', '.'))
#         return valor
    
#     def process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
#         """Procesa el DataFrame para normalizar datos y convertir valores monetarios"""
#         # Crear copia para no modificar el original
#         df_processed = df.copy()
        
#         # Convertir valores monetarios
#         for col in df_processed.columns:
#             if df_processed[col].dtype == object:  # Solo procesar columnas de texto
#                 try:
#                     # Verificar si la columna contiene valores monetarios
#                     if df_processed[col].str.contains('\$').any():
#                         df_processed[col] = df_processed[col].apply(self.convertir_moneda)
#                 except:
#                     pass  # Si no se puede procesar, mantener como está
        
#         # Eliminar filas donde todos los valores numéricos son NaN o 0
#         numeric_cols = df_processed.select_dtypes(include=[np.number]).columns
#         if len(numeric_cols) > 0:
#             mask = ~((df_processed[numeric_cols] == 0) | df_processed[numeric_cols].isna()).all(axis=1)
#             df_processed = df_processed[mask].reset_index(drop=True)
        
#         return df_processed
    
#     def create_documents(self, df: pd.DataFrame) -> Tuple[List[str], List[Dict], List[str]]:
#         """Crea documentos, metadatos e IDs para ChromaDB"""
#         documents = []
#         metadatas = []
#         ids = []
        
#         for idx, row in df.iterrows():
#             try:
#                 # Formato para valores monetarios
#                 def formato_moneda(valor):
#                     if pd.notna(valor) and isinstance(valor, (int, float)):
#                         return f"${valor:.2f}"
#                     return str(valor) if pd.notna(valor) else "N/A"
                
#                 # Crear texto descriptivo con todas las columnas disponibles
#                 partes = []
                
#                 # Añadir información por categorías si están disponibles
#                 if 'Local' in df.columns and pd.notna(row['Local']):
#                     partes.append(f"En el local {row['Local']}")
                
#                 if 'fecha' in df.columns and pd.notna(row['fecha']):
#                     partes.append(f"con fecha {row['fecha']}")
                
#                 # Añadir valores monetarios con formato
#                 if 'Base0' in df.columns and pd.notna(row['Base0']):
#                     partes.append(f"se registró una base imponible al 0% de {formato_moneda(row['Base0'])}")
                
#                 if 'Base<>0' in df.columns and pd.notna(row['Base<>0']):
#                     partes.append(f"una base imponible distinta de 0% de {formato_moneda(row['Base<>0'])}")
                
#                 if 'Impuestos' in df.columns and pd.notna(row['Impuestos']):
#                     partes.append(f"con impuestos de {formato_moneda(row['Impuestos'])}")
                
#                 if 'Venta-Impuesto' in df.columns and pd.notna(row['Venta-Impuesto']):
#                     partes.append(f"resultando en una venta sin impuesto de {formato_moneda(row['Venta-Impuesto'])}")
                
#                 col_suma = next((col for col in df.columns if 'suma' in col.lower() or 'total' in col.lower()), None)
#                 if col_suma and pd.notna(row[col_suma]):
#                     partes.append(f"y un total sin impuestos adicionales de {formato_moneda(row[col_suma])}")
                
#                 # Si hay columnas que no hemos manejado específicamente, añadirlas
#                 otras_columnas = [col for col in df.columns if col not in ['Local', 'fecha', 'Base0', 'Base<>0', 
#                                                                           'Impuestos', 'Venta-Impuesto'] 
#                                  and not (('suma' in col.lower() or 'total' in col.lower()) and col == col_suma)]
                
#                 for col in otras_columnas:
#                     if pd.notna(row[col]):
#                         if isinstance(row[col], (int, float)):
#                             partes.append(f"{col}: {formato_moneda(row[col])}")
#                         else:
#                             partes.append(f"{col}: {row[col]}")
                
#                 # Unir partes en un documento
#                 document = " ".join(partes) + "."
#                 documents.append(document)
                
#                 # Crear metadatos
#                 metadata = {}
#                 if 'Local' in df.columns and pd.notna(row['Local']):
#                     metadata['local'] = str(row['Local'])
#                 if 'fecha' in df.columns and pd.notna(row['fecha']):
#                     metadata['fecha'] = str(row['fecha'])
                
#                 metadatas.append(metadata)
                
#                 # Generar ID único
#                 ids.append(f"id{idx+1}")
                
#             except Exception as e:
#                 logger.error(f"Error procesando fila {idx}: {str(e)}")
        
#         return documents, metadatas, ids

# class RAGRetriever:
#     def __init__(self):
#         self.chroma_client = chromadb.Client()
#         self.collection_name = settings["collection_name"]
#         self.processor = DataProcessor()
        
#     def initialize_collection(self, data_path: str) -> bool:
#         """Configura la colección de ChromaDB a partir de un archivo CSV o TXT"""
#         try:
#             # Eliminar colección si existe
#             try:
#                 self.chroma_client.delete_collection(self.collection_name)
#                 logger.info(f"Colección anterior {self.collection_name} eliminada")
#             except:
#                 pass
            
#             # Crear nueva colección
#             collection = self.chroma_client.create_collection(name=self.collection_name)
            
#             # Determinar el tipo de archivo por extensión
#             if data_path.lower().endswith('.csv'):
#                 # Cargar CSV directamente con pandas
#                 logger.info(f"Cargando datos CSV desde {data_path}")
#                 df = pd.read_csv(data_path)
                
#             elif data_path.lower().endswith('.txt'):
#                 # Procesar archivo TXT con formato específico
#                 logger.info(f"Cargando datos TXT desde {data_path}")
#                 df = self.cargar_datos_txt(data_path)
                
#             else:
#                 # Intentar cargar como CSV por defecto
#                 logger.warning(f"Tipo de archivo no reconocido, intentando como CSV: {data_path}")
#                 df = pd.read_csv(data_path)
            
#             # Verificar que hay datos
#             if df.empty:
#                 raise ValueError("No se encontraron datos en el archivo")
            
#             logger.info(f"Columnas detectadas: {df.columns.tolist()}")
            
#             # Procesar datos sin verificar columnas específicas
#             df_processed = self.processor.process_dataframe(df)
#             logger.info(f"Datos procesados: {len(df_processed)} registros válidos")
            
#             # Crear documentos
#             documents, metadatas, ids = self.processor.create_documents(df_processed)
            
#             if not documents:
#                 raise ValueError("No se pudieron crear documentos a partir de los datos")
            
#             # Añadir documentos a ChromaDB
#             batch_size = 50  # Procesar en lotes para evitar problemas de memoria
#             for i in range(0, len(documents), batch_size):
#                 end_idx = min(i + batch_size, len(documents))
#                 collection.add(
#                     documents=documents[i:end_idx],
#                     metadatas=metadatas[i:end_idx],
#                     ids=ids[i:end_idx]
#                 )
            
#             # Añadir resumen estadístico si hay datos suficientes
#             if len(df_processed) >= 5:
#                 self.agregar_estadisticas(collection, df_processed)
            
#             logger.info(f"Datos cargados en ChromaDB: {len(documents)} documentos")
#             return True
            
#         except Exception as e:
#             logger.error(f"Error configurando la colección: {str(e)}")
#             # Crear colección de respaldo con mensaje de error
#             collection = self.chroma_client.create_collection(name=self.collection_name)
#             collection.add(
#                 documents=["Error cargando datos: " + str(e)],
#                 ids=["error_1"]
#             )
#             return False
    
#     def cargar_datos_txt(self, archivo_txt: str) -> pd.DataFrame:
#         """Carga datos desde un archivo TXT con formato específico"""
#         with open(archivo_txt, 'r', encoding='utf-8') as f:
#             lineas = f.readlines()
        
#         # Procesar líneas para detectar estructura
#         datos = []
#         local_actual = None
        
#         for linea in lineas:
#             linea = linea.strip()
#             if not linea:
#                 continue
            
#             # Dividir por tabulaciones
#             partes = linea.split('\t')
            
#             # Detectar tipo de línea
#             primera_parte = partes[0]
            
#             # Detectar si es un código de local (ej: "002-GUASMO")
#             if re.match(r'\d{3}-[A-Z\-]+', primera_parte):
#                 local_actual = primera_parte
#                 # Si hay más datos en esta línea además del local
#                 if len(partes) > 1:
#                     fila = {'Local': local_actual}
#                     # La segunda columna es probablemente la fecha
#                     if len(partes) > 1:
#                         fila['fecha'] = partes[1]
#                     # Las siguientes son valores numéricos
#                     nombres_columnas = ['Base0', 'Base<>0', 'Impuestos', 'Venta-Impuesto', 
#                                        'Suma de total_venta_sinimpuestos adicionales']
#                     for i in range(2, min(len(partes), len(nombres_columnas) + 2)):
#                         fila[nombres_columnas[i-2]] = partes[i]
                    
#                     datos.append(fila)
            
#             # Detectar si es una fecha (ej: "1-mar")
#             elif re.match(r'\d{1,2}-[a-z]{3}', primera_parte) and local_actual:
#                 fila = {'Local': local_actual, 'fecha': primera_parte}
                
#                 # Las columnas restantes son valores numéricos
#                 nombres_columnas = ['Base0', 'Base<>0', 'Impuestos', 'Venta-Impuesto', 
#                                    'Suma de total_venta_sinimpuestos adicionales']
#                 for i in range(1, min(len(partes), len(nombres_columnas) + 1)):
#                     fila[nombres_columnas[i-1]] = partes[i]
                
#                 datos.append(fila)
            
#             # Ignorar líneas de total
#             elif primera_parte.startswith('Total'):
#                 continue
        
#         # Crear DataFrame
#         df = pd.DataFrame(datos)
        
#         # Convertir valores monetarios
#         for col in df.columns:
#             if col != 'Local' and col != 'fecha':
#                 df[col] = df[col].apply(self.processor.convertir_moneda)
        
#         return df
    
#     def agregar_estadisticas(self, collection, df: pd.DataFrame) -> None:
#         """Agrega documentos de estadísticas a la colección"""
#         try:
#             # Obtener columnas numéricas
#             numeric_cols = df.select_dtypes(include=[np.number]).columns
            
#             if len(numeric_cols) > 0:
#                 # Calcular totales por local si existe columna Local
#                 if 'Local' in df.columns:
#                     totales_por_local = df.groupby('Local')[numeric_cols].sum().reset_index()
                    
#                     for idx, row in totales_por_local.iterrows():
#                         local = row['Local']
#                         texto = f"Resumen total del local {local}: "
                        
#                         for col in numeric_cols:
#                             texto += f"{col}: ${row[col]:.2f}, "
                        
#                         texto = texto.rstrip(", ") + "."
                        
#                         collection.add(
#                             documents=[texto],
#                             metadatas=[{"tipo": "estadistica", "local": local}],
#                             ids=[f"stat_local_{idx}"]
#                         )
                
#                 # Calcular estadísticas generales
#                 total_general = df[numeric_cols].sum()
#                 texto_general = "Resumen general de todos los locales: "
                
#                 for col in numeric_cols:
#                     texto_general += f"Total {col}: ${total_general[col]:.2f}, "
                
#                 texto_general = texto_general.rstrip(", ") + "."
                
#                 collection.add(
#                     documents=[texto_general],
#                     metadatas=[{"tipo": "estadistica", "local": "todos"}],
#                     ids=["stat_general"]
#                 )
                
#         except Exception as e:
#             logger.error(f"Error generando estadísticas: {str(e)}")
    
#     async def query(self, user_query: str, k: int = 6) -> Dict[str, Any]:
#         """Realiza una consulta y recupera documentos relevantes"""
#         try:
#             collection = self.chroma_client.get_collection(self.collection_name)
            
#             # Consultar ChromaDB
#             results = collection.query(
#                 query_texts=[user_query],
#                 n_results=k
#             )
            
#             # Obtener documentos e ids
#             documents = results["documents"][0]
            
#             # Agregar estadísticas generales para consultas de resumen
#             if any(palabra in user_query.lower() for palabra in ["total", "resumen", "estadística", "general"]):
#                 # Buscar documentos de estadísticas
#                 try:
#                     stats_results = collection.query(
#                         query_texts=["estadísticas resumen general"],
#                         where={"tipo": "estadistica"},
#                         n_results=4
#                     )
#                     # Añadir al contexto si no están ya incluidos
#                     for doc in stats_results["documents"][0]:
#                         if doc not in documents:
#                             documents.append(doc)
#                 except:
#                     pass  # Si no se puede filtrar por tipo, continuar
            
#             # Construir contexto completo
#             context = "\n\n".join(documents)
            
#             return {
#                 "context": context,
#                 "has_relevant_info": len(documents) > 0
#             }
                
#         except Exception as e:
#             logger.error(f"Error consultando ChromaDB: {str(e)}")
#             return {
#                 "context": f"Error recuperando información: {str(e)}",
#                 "has_relevant_info": False
#             }