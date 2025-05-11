
import boto3
import pandas as pd
from pymongo import MongoClient
import os
import logging

# --- Configurar logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuraciones ---
BUCKET_NAME = 'proy-cloud-bucket'
ANALISIS_FOLDER = 'Analisis/'
TEMP_DIR = '/tmp/mongodb_exports/'  # Directorio temporal para archivos CSV

# --- Asegurar que el directorio temporal exista ---
os.makedirs(TEMP_DIR, exist_ok=True)

# --- Conexiones ---
try:
    s3_client = boto3.client('s3')
    mongo_client = MongoClient('mongodb://localhost:27017/')
    db = mongo_client["smartstock_db"]
    logger.info("Conexiones establecidas correctamente.")
except Exception as e:
    logger.error(f"Error al establecer conexiones: {e}")
    raise

def exportar_y_subir(nombre_coleccion, nombre_csv):
    """
    Exporta una colección de MongoDB a CSV y la sube a S3
    
    Args:
        nombre_coleccion (str): Nombre de la colección en MongoDB
        nombre_csv (str): Nombre del archivo CSV a generar
    """
    try:
        # Verificar si la colección existe
        if nombre_coleccion not in db.list_collection_names():
            logger.warning(f"La colección {nombre_coleccion} no existe en la base de datos.")
            return
        
        # Obtener datos
        datos = list(db[nombre_coleccion].find({}, {'_id': 0}))
        
        if not datos:
            logger.warning(f"La colección {nombre_coleccion} está vacía.")
            return
            
        # Convertir a DataFrame
        df = pd.DataFrame(datos)
        
        # Ruta completa del archivo temporal
        ruta_archivo = os.path.join(TEMP_DIR, nombre_csv)
        
        # Guardar CSV temporal
        df.to_csv(ruta_archivo, index=False)
        logger.info(f"Archivo {nombre_csv} creado con {len(df)} registros.")
        
        # Subir al bucket
        s3_client.upload_file(ruta_archivo, BUCKET_NAME, f"{ANALISIS_FOLDER}{nombre_csv}")
        logger.info(f"Archivo {nombre_csv} subido exitosamente al bucket S3.")
        
        # Eliminar archivo temporal
        os.remove(ruta_archivo)
        logger.info(f"Archivo temporal {nombre_csv} eliminado.")
        
    except Exception as e:
        logger.error(f"Error al procesar la colección {nombre_coleccion}: {e}")

def main():
    """Función principal que procesa todas las colecciones"""
    try:
        logger.info("Iniciando proceso de exportación y carga a S3...")
        
        # Lista de colecciones a exportar
        colecciones = [
            ('ventas_aggregadas', 'ventas_aggregadas.csv'),
            ('alertas_stock', 'alertas_stock.csv'),
            ('estacionalidad', 'estacionalidad.csv')
        ]
        
        # Procesar cada colección
        for coleccion, archivo in colecciones:
            exportar_y_subir(coleccion, archivo)
            
        logger.info("Proceso completado exitosamente.")
        
    except Exception as e:
        logger.error(f"Error en el proceso principal: {e}")
    finally:
        # Cerrar conexiones
        mongo_client.close()
        logger.info("Conexiones cerradas.")

if __name__ == "__main__":
    main()

