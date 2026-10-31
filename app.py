import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
import io
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

# 1. Carga del archivo
archivo_subido = st.file_uploader("Selecciona el archivo CSV del turno", type=["csv"])

# Resetear estado de la sesión si se cambia el archivo
if archivo_subido is None and "borrador_correo" in st.session_state:
    del st.session_state["borrador_correo"]

if archivo_subido is not None:
    try:
        # Leer el archivo con Pandas
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
                errores.append("Estructura incorrecta. Faltan columnas requeridas o hay columnas adicionales.")

        if errores:
            for error in errores:
                st.error(error)
            st.stop()
            
        else:
            st.success("¡Archivo cargado y validado correctamente!")
            
            # Listas de analitos
            analitos_cuantitativos = [
                "Grados_Brix", "Volumenes_CO2", "pH", "Acidez_Titulable", 
                "Volumen_Llenado", "Presion_Interna", "Mohos_Levaduras", "Mesofilos_Aerobios"
            ]
            analitos_cualitativos = ["Integridad_Cierre", "Apariencia_Color", "Sabor_Aroma"]

            # 2. GRÁFICOS INTERACTIVOS (PLOTLY)
            st.markdown("---")
            st.subheader("📊 Comportamiento de los Analitos")
            
            tabs = st.tabs([a.replace('_', ' ') for a in analitos_cuantitativos] + ["Cualitativos"])
            
            for i, analito in enumerate(analitos_cuantitativos):
                with tabs[i]:
                    col_valor, col_li, col_ls = f"{analito}_Valor", f"{analito}_LI", f"{analito}_LS"
                    fuera_limite = df[(df[col_valor] < df[col_li]) | (df[col_valor] > df[col_ls])]
                    dentro_limite = df[(df[col_valor] >= df[col_li]) & (df[col_valor] <= df[col_ls])]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=df["Hora_Muestreo"], y=df[col_ls], mode='lines', name='Límite Superior', line=dict(color='orange', dash='dash')))
                    fig.add_trace(go.Scatter(x=df["Hora_Muestreo"], y=df[col_li], mode='lines', name='Límite Inferior', line=dict(color='orange', dash='dash')))
                    fig.add_trace(go.Scatter(x=df["Hora_Muestreo"], y=df[col_valor], mode='lines', name='Tendencia', line=dict(color='lightblue'), hoverinfo='skip'))
                    fig.add_trace(go.Scatter(x=dentro_limite["Hora_Muestreo"], y=dentro_limite[col_valor], mode='markers', name='Dentro de Norma', marker=dict(color='blue', size=8)))
                    
                    if not fuera_limite.empty:
                        fig.add_trace(go.Scatter(x=fuera_limite["Hora_Muestreo"], y=fuera_limite[col_valor], mode='markers', name='Fuera de Norma', marker=dict(color='red', size=10, symbol='x')))
                    
                    fig.update_layout(title=f"Evolución de {analito.replace('_', ' ')}", xaxis_title="Hora de Muestreo", yaxis_title="Valor Medido")
                    st.plotly_chart(fig, use_container_width=True)

            with tabs[-1]:
                fallos_cualitativos = []
                for analito in analitos_cualitativos:
                    cantidad_fallos = (df[f"{analito}_Valor"] != df[f"{analito}_Esperado"]).sum()
                    fallos_cualitativos.append({"Analito": analito.replace('_', ' '), "Fallos": cantidad_fallos})
                
                fig_barras = px.bar(pd.DataFrame(fallos_cualitativos), x="Analito", y="Fallos", text="Fallos", title="Desviaciones Cualitativas", color="Fallos", color_continuous_scale="Reds")
                st.plotly_chart(fig_barras, use_container_width=True)
            
            # 3. ANÁLISIS DE RECHAZOS Y BORRADOR CON GEMINI
            st.markdown("---")
            st.subheader("🤖 Análisis de IA y Generación de Correo")
            
            rechazos = df[df["Estado_Calidad"].str.upper() == "RECHAZADO"]
            
            # Generar pre-resumen para Gemini
            if rechazos.empty:
                pre_resumen = "Estado: 0 rechazos. Todo estable."
            else:
                lotes = ", ".join(rechazos["Lote_Produccion"].astype(str).unique())
                lineas = ", ".join(rechazos["Linea_Produccion"].astype(str).unique())
                
                analitos_fallidos = []
                for col in analitos_cuantitativos:
                    if any((rechazos[f"{col}_Valor"] < rechazos[f"{col}_LI"]) | (rechazos[f"{col}_Valor"] > rechazos[f"{col}_LS"])):
                        analitos_fallidos.append(col.replace("_", " "))
                for col in analitos_cualitativos:
                    if any(rechazos[f"{col}_Valor"] != rechazos[f"{col}_Esperado"]):
                        analitos_fallidos.append(col.replace("_", " "))
                        
                mensajes = " ".join(rechazos["Mensaje_Supervisor"].dropna().unique())
                pre_resumen = f"Estado: Rechazos detectados. Lote(s): {lotes}. Línea(s): {lineas}. Analitos fuera de norma: {', '.join(set(analitos_fallidos))}. Acción sugerida: {mensajes}"
            
            st.info(f"**Datos enviados a Gemini:**\n{pre_resumen}")

            # Generar Imagen Consolidada con Matplotlib
            fig_mpl, ax = plt.subplots(figsize=(8, 2.5))
            ax.axis('tight')
            ax.axis('off')
            
            if rechazos.empty:
                resumen_df = df[['Fecha_Analisis', 'Lote_Produccion', 'Linea_Produccion', 'Estado_Calidad']].head(1).copy()
                resumen_df['Estado_Calidad'] = "100% Aprobado"
                titulo_grafico = "Resumen del Turno: ESTABLE"
            else:
                resumen_df = rechazos[['Fecha_Analisis', 'Lote_Produccion', 'Linea_Produccion', 'Estado_Calidad']].drop_duplicates()
                titulo_grafico = "Evidencia de Fallos (Lotes Rechazados)"
                
            ax.set_title(titulo_grafico, fontsize=12, fontweight='bold', color='darkblue')
            tabla = ax.table(cellText=resumen_df.values, colLabels=resumen_df.columns, loc='center', cellLoc='center')
            tabla.scale(1, 1.5)
            
            # Guardar figura en memoria RAM (BytesIO)
            buf = io.BytesIO()
            plt.savefig(buf, format="png", bbox_inches='tight', dpi=150)
            buf.seek(0)
            st.image(buf, caption="Gráfica Matplotlib (Lista para incrustarse en el correo)")
            
            # Llamada a Gemini
            system_prompt = """Eres el sistema automatizado de notificaciones del Laboratorio de Calidad de una línea de envasado de gaseosas. Tu único objetivo es redactar un correo electrónico profesional dirigido al Supervisor de Línea, basándote ESTRICTAMENTE en el resumen de datos que recibirás.

REGLAS DE REDACCIÓN:
1. Turno Impecable (0 rechazos): Si el resumen indica que no hay rechazos, redacta un correo de "Turno sin novedades". El tono debe ser FORMAL y TRANQUILIZADOR, indicando brevemente que todos los parámetros de calidad del turno se mantuvieron estables dentro de los límites y no se requiere acción.
2. Turno con Fallos: Si el resumen contiene lotes rechazados, el tono debe ser FORMAL y de URGENCIA. Resalta claramente la línea de producción y el lote afectado.
3. Consolidación: Usa viñetas para listar los analitos fuera de norma reportados en el resumen para que la lectura sea rápida.
4. Acciones Correctivas (CRÍTICO): Extrae las acciones correctivas ESTRICTAMENTE del texto proporcionado (que proviene del Mensaje del Supervisor del laboratorio). BAJO NINGUNA CIRCUNSTANCIA inventes, asumas o sugieras acciones operativas, mecánicas o técnicas por tu cuenta.
5. Cero Alucinaciones: NUNCA inventes números de análisis, valores, lotes, fechas o analitos que no estén explícitamente en el texto de entrada.
6. Firma: Cierra el correo firmando como "Sistema Automatizado de Monitoreo de Calidad PT". No agregues nombres propios."""

            if "borrador_correo" not in st.session_state:
                with st.spinner("Redactando correo con IA..."):
                    try:
                        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                        response = client.models.generate_content(
                            model="gemini-3.5-flash-lite",
                            contents=pre_resumen,
                            config=types.GenerateContentConfig(
                                system_instruction=system_prompt,
                                temperature=0.1
                            )
                        )
                        st.session_state.borrador_correo = response.text
                    except Exception as e:
                        st.error(f"Error al conectar con Gemini: Verifica tu API Key. Detalle: {e}")
                        st.session_state.borrador_correo = None
            
            if st.session_state.borrador_correo:
                st.text_area("Borrador generado (Puedes editarlo antes de enviar):", value=st.session_state.borrador_correo, height=250, key="texto_correo")
                
                # --- AQUÍ IRÁ EL ÚLTIMO PASO: ENVIAR POR CORREO (SMTP) ---
                st.button("Validar y Enviar Correo", disabled=True, help="El envío SMTP se implementará en el próximo paso.")
                
    except pd.errors.EmptyDataError:
        st.error("El archivo está vacío o tiene un formato incorrecto.")
    except Exception as e:
        st.error(f"Ocurrió un error inesperado: {e}")