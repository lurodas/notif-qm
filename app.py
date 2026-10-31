import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

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

# 1. Carga del archivo
archivo_subido = st.file_uploader("Selecciona el archivo CSV del turno", type=["csv"])

if archivo_subido is not None:
    try:
        # Leer el archivo con Pandas
        df = pd.read_csv(archivo_subido)
        
        # Validaciones de la especificación
        errores = []
        
        # A. Validar que no esté vacío (0 líneas)
        if df.empty:
            errores.append("El archivo está vacío. No contiene resultados de análisis.")
            
        # B. Validar que no supere las 100 líneas
        elif len(df) > 100:
            errores.append(f"El archivo es demasiado grande. Contiene {len(df)} líneas, pero el máximo permitido es 100.")
            
        # C. Validar la estructura exacta de columnas
        else:
            columnas_archivo = list(df.columns)
            if len(columnas_archivo) != 36 or not all(col in columnas_archivo for col in COLUMNAS_ESPERADAS):
                errores.append("El archivo no tiene la estructura correcta. Debe contener exactamente las 36 columnas requeridas para el análisis de calidad.")

        # Mostrar resultados de la validación
        if errores:
            for error in errores:
                st.error(error)
            st.stop() # Detiene la ejecución para no procesar datos malos
            
        else:
            st.success("¡Archivo cargado y validado correctamente!")
            st.write(f"Se encontraron {len(df)} muestras listas para analizar.")
            
            # Mostrar una vista previa de los datos
            st.dataframe(df.head())
            
            # 2. GRÁFICOS INTERACTIVOS (PLOTLY)
            st.markdown("---")
            st.subheader("📊 Comportamiento de los Analitos (Cuantitativos)")
            
            # Lista base de analitos cuantitativos
            analitos_cuantitativos = [
                "Grados_Brix", "Volumenes_CO2", "pH", "Acidez_Titulable", 
                "Volumen_Llenado", "Presion_Interna", "Mohos_Levaduras", "Mesofilos_Aerobios"
            ]