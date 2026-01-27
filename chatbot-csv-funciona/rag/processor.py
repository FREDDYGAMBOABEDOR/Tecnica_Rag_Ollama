import pandas as pd
import logging
from typing import Tuple, List, Dict, Any

logger = logging.getLogger(__name__)

class DataProcessor:
    @staticmethod
    def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
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
    
    @staticmethod
    def create_documents(df: pd.DataFrame) -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
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