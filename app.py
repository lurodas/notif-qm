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
            
            # Usamos pestañas (tabs) para una navegación más limpia
            tabs = st.tabs([a.replace('_', ' ') for a in analitos_cuantitativos])
            
            for i, analito in enumerate(analitos_cuantitativos):
                with tabs[i]:
                    col_valor = f"{analito}_Valor"
                    col_li = f"{analito}_LI"
                    col_ls = f"{analito}_LS"
                    
                    # Identificar puntos fuera de límite para marcarlos en rojo
                    fuera_limite = df[(df[col_valor] < df[col_li]) | (df[col_valor] > df[col_ls])]
                    dentro_limite = df[(df[col_valor] >= df[col_li]) & (df[col_valor] <= df[col_ls])]
                    
                    fig = go.Figure()
                    
                    # Límites superior e inferior
                    fig.add_trace(go.Scatter(x=df["Hora_Muestreo"], y=df[col_ls], mode='lines', name='Límite Superior', line=dict(color='orange', dash='dash')))
                    fig.add_trace(go.Scatter(x=df["Hora_Muestreo"], y=df[col_li], mode='lines', name='Límite Inferior', line=dict(color='orange', dash='dash')))
                    
                    # Puntos correctos y líneas de tendencia
                    fig.add_trace(go.Scatter(x=df["Hora_Muestreo"], y=df[col_valor], mode='lines', name='Tendencia', line=dict(color='lightblue'), hoverinfo='skip'))
                    fig.add_trace(go.Scatter(x=dentro_limite["Hora_Muestreo"], y=dentro_limite[col_valor], mode='markers', name='Dentro de Norma', marker=dict(color='blue', size=8)))
                    
                    # Puntos defectuosos (rojos)
                    if not fuera_limite.empty:
                        fig.add_trace(go.Scatter(x=fuera_limite["Hora_Muestreo"], y=fuera_limite[col_valor], mode='markers', name='Fuera de Norma', marker=dict(color='red', size=10, symbol='x')))
                    
                    fig.update_layout(title=f"Evolución de {analito.replace('_', ' ')}", xaxis_title="Hora de Muestreo", yaxis_title="Valor Medido", hovermode="x unified")
                    st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            st.subheader("📈 Frecuencia de Fallos (Cualitativos)")
            
            analitos_cualitativos = ["Integridad_Cierre", "Apariencia_Color", "Sabor_Aroma"]
            fallos_cualitativos = []
            
            for analito in analitos_cualitativos:
                col_esperado = f"{analito}_Esperado"
                col_valor = f"{analito}_Valor"
                # Contamos cuántas veces el valor obtenido es distinto al esperado
                cantidad_fallos = (df[col_valor] != df[col_esperado]).sum()
                fallos_cualitativos.append({"Analito": analito.replace('_', ' '), "Fallos": cantidad_fallos})
                
            df_fallos = pd.DataFrame(fallos_cualitativos)
            
            fig_barras = px.bar(df_fallos, x="Analito", y="Fallos", text="Fallos", title="Recuento de Desviaciones Cualitativas", color="Fallos", color_continuous_scale="Reds")
            st.plotly_chart(fig_barras, use_container_width=True)
            
            # --- AQUÍ IRA EL SIGUIENTE PASO: RESUMEN PANDAS, MATPLOTLIB Y GEMINI ---
            
    except pd.errors.EmptyDataError:
        st.error("El archivo está completamente vacío o no tiene el formato correcto.")
    except Exception as e:
        st.error(f"Ocurrió un problema inesperado al leer el archivo: {e}")