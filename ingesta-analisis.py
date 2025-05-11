import boto3
import pandas as pd
from pymongo import MongoClient

# --- Configuraciones ---
BUCKET_NAME = 'proy'
ANALISIS_FOLDER = 'Analisis/'

# --- Conexiones ---
s3_client = boto3.client('s3')
mongo_client = MongoClient('mongodb://localhost:27017/')
db = mongo_client["smartstock_db"]

def exportar_y_subir(nombre_coleccion, nombre_csv):
    datos = list(db[nombre_coleccion].find({}, {'_id': 0}))
    df = pd.DataFrame(datos)

    # Guardar CSV temporal
    df.to_csv(nombre_csv, index=False)

    # Subir al bucket
    s3_client.upload_file(nombre_csv, BUCKET_NAME, f"{ANALISIS_FOLDER}{nombre_csv}")
    print(f"{nombre_csv} subido exitosamente al bucket.")

def main():
    exportar_y_subir('ventas_aggregadas', 'ventas_aggregadas.csv')
    exportar_y_subir('alertas_stock', 'alertas_stock.csv')
    exportar_y_subir('estacionalidad', 'estacionalidad.csv')

if __name__ == "__main__":
    main()

