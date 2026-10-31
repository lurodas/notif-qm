import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
import io
import smtplib
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from google import genai
from google.genai import types

# Configuración básica de la página
st.set_page_config(page_title="Notificador de Calidad PT", page_icon="📊", layout="wide")

st.title("Notificador de Muestras de Producto Terminado")
st.write("Sube el archivo con los resultados del laboratorio para su análisis.")

# Lista exacta de las 36 columnas requeridas por la especificación
COLUMNAS_ESPERADAS = [
    "Fecha_Analisis", "Hora_Muestreo", "Lote_Produccion", "Linea_Produccion",
    "Grados_Brix_LI", "Grados_Brix_Valor", "Grados_Brix_LS",
    "Volumenes_CO2_LI", "Volumenes_CO2_Valor", "Volumenes_CO2_LS",
    "pH_LI", "pH_Valor", "pH_LS",
    "Acidez_Titulable_LI", "Acidez_Titulable_Valor", "Acidez_Titulable_LS",
    "Volumen_Llenado_LI", "Volumen_Llenado_Valor", "Volumen_Llenado_LS",
    "Integridad_Cierre_Esperado", "Integridad_Cierre_Valor",
    "Presion_Interna_LI", "Presion_Interna_Valor", "Presion_Interna_LS",
    "Apariencia_Color_Esperado", "Apariencia_Color_Valor",
    "Sabor_Aroma_Esperado", "Sabor_Aroma_Valor",
    "Mohos_Levaduras_LI", "Mohos_Levaduras_Valor", "Mohos_Levaduras_LS",
    "Mesofilos_Aerobios_LI", "Mesofilos_Aerobios_Valor", "Mesofilos_Aerobios_LS",
    "Estado_Calidad", "Mensaje_Supervisor"
]

def validar_correo(correo):
    """Valida que el texto sea exactamente un (1) correo electrónico válido."""
    patron = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(patron, correo.strip()) is not None

# 1. Carga del archivo
archivo_subido = st.file_uploader("Selecciona el archivo CSV del turno", type=["csv"])

# Resetear estado de la sesión si se cambia el archivo
if archivo_subido is None and "borrador_correo" in st.session_state:
    del st.session_state["borrador_correo"]

if archivo_subido is not None:
    try:
        df = pd.read_csv(archivo_subido)
        
        # Validaciones de la especificación
        errores = []
        if df.empty:
            errores.append("El archivo está vacío. No contiene resultados de análisis.")
        elif len(df) > 100:
            errores.append(f"El archivo es demasiado grande. Contiene {len(df)} líneas, máximo permitido: 100.")
        else:
            columnas_archivo = list(df.columns)
            if len(columnas_archivo) != 36 or not all(col in columnas_archivo for col in COLUMNAS_ESPERADAS):
                errores.append("Estruct