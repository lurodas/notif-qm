import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import io
import smtplib
from email.message import EmailMessage
from google import genai
from google.genai import types
import re

# ==========================================
# CONFIGURACIÓN Y CONSTANTES
# ==========================================
st.set_page_config(page_title="Control de Calidad PT", layout="wide")
MODELO = "gemini-3.5-flash-lite"

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

ANALITOS_NUMERICOS = ["Grados_Brix", "Volumenes_CO2", "pH", "Acidez_Titulable", "Volumen_Llenado", "Presion_Interna", "Mohos_Levaduras", "Mesofilos_Aerobios"]
ANALITOS_CUALITATIVOS = ["Integridad_Cierre", "Apariencia_Color", "Sabor_Aroma"]

# ==========================================
# FUNCIONES DE AYUDA Y VALIDACIÓN
# ==========================================
def validar_correo(correo):
    patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(patron, correo) is not None

def generar_pre_resumen(df):
    rechazos = df[df["Estado_Calidad"].str.upper() == "RECHAZADO"]
    if rechazos.empty:
        return "Estado: 0 rechazos. Todo estable. Todos los parámetros dentro de los límites."
    
    resumen = "Estado: Rechazos detectados.\n"
    for _, fila in rechazos.iterrows():
        resumen += f"- Lote: {fila['Lote_Produccion']} | Línea: {fila['Linea_Produccion']}\n"
        resumen += f"  Acción sugerida: {fila['Mensaje_Supervisor']}\n"
    return resumen

def generar_imagen_matplotlib(df):
    plt.switch_backend('Agg') # Evitar problemas de hilos en Streamlit
    fig, axes = plt.subplots(4, 3, figsize=(15, 15))
    fig.suptitle('Resumen Consolidado de Analitos del Turno', fontsize=16)
    axes = axes.flatten()
    
    for i, analito in enumerate(ANALITOS_NUMERICOS):
        ax = axes[i]
        ax.plot(df["Hora_Muestreo"], df[f"{analito}_Valor"], marker='o', label='Valor')
        ax.axhline(df[f"{analito}_LS"].iloc[0], color='r', linestyle='--', label='Límite Sup')
        ax.axhline(df[f"{analito}_LI"].iloc[0], color='r', linestyle='--', label='Límite Inf')
        ax.set_title(analito)
        ax.tick_params(axis='x', rotation=45)
        
    for i, analito in enumerate(ANALITOS_CUALITATIVOS, start=len(ANALITOS_NUMERICOS)):
        ax = axes[i]
        fallos = df[df[f"{analito}_Valor"].str.upper() != df[f"{analito}_Esperado"].str.upper()]
        conteo = fallos["Lote_Produccion"].value_counts() if not fallos.empty else pd.Series({"Sin Fallos": 1})
        conteo.plot(kind='bar', ax=ax, color='orange')
        ax.set_title(f"Fallos en {analito}")
        
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    return buf.read()

def redactar_correo_ia(resumen):
    instrucciones = """Eres el sistema automatizado de notificaciones del Laboratorio de Calidad.
    REGLAS:
    1. Si hay 0 rechazos, redacta un correo "Turno sin novedades", tono FORMAL y TRANQUILIZADOR.
    2. Si hay fallos, tono FORMAL y URGENTE detallando la línea y lote.
    3. Usa viñetas.
    4. Extrae acciones correctivas ESTRICTAMENTE del texto proporcionado. No inventes soluciones.
    5. Cero alucinaciones.
    6. Entrega solo el "Asunto:" seguido del cuerpo del correo en HTML, listo para enviar. Usa estilos CSS en línea."""
    
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        response = client.models.generate_content(
            model=MODELO,
            contents=resumen,
            config=types.GenerateContentConfig(
                temperature=0.1,
                system_instruction=instrucciones
            )
        )
        return response.text
    except Exception as e:
        st.error(f"Error al conectar con Gemini para el correo: {e}")
        return None

def enviar_correo(asunto, cuerpo_html, imagen_bytes, correo_copia):
    try:
        msg = EmailMessage()
        msg['Subject'] = asunto.replace("Asunto: ", "").strip()
        msg['From'] = st.secrets["EMAIL_USERNAME"]
        msg['To'] = st.secrets["EMAIL_RECIPIENT"]
        msg['Cc'] = correo_copia
        
        msg.add_alternative(cuerpo_html, subtype='html')
        msg.add_attachment(imagen_bytes, maintype='image', subtype='png', filename='reporte_calidad.png')
        
        with smtplib.SMTP_SSL(st.secrets["SMTP_SERVER"], st.secrets["SMTP_PORT"]) as server:
            server.login(st.secrets["EMAIL_USERNAME"], st.secrets["EMAIL_PASSWORD"])
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Error de red o autenticación al enviar el correo: {e}")
        return False

# ==========================================
# INTERFAZ DE USUARIO (UI)
# ==========================================
st.markdown("### 🧪 Notificador de Muestras - Producto Terminado")
st.info("🔗 [Descargar Archivo de Demostración (CSV)](https://github.com/lurodas/notif-qm/blob/main/ejemplos/Resultados_60_Lineas_Con_Limites.csv)")

archivo = st.file_uploader("Sube el archivo CSV con los resultados del laboratorio", type=["csv"])

if archivo is not None:
    # 1. Validación de Pandas
    df = pd.read_csv(archivo)
    
    if len(df) == 0:
        st.error("El archivo está vacío (0 líneas). Por favor, revisa los datos.")
        st.stop()
    if len(df) > 100:
        st.error(f"El archivo supera las 100 líneas permitidas (tiene {len(df)}).")
        st.stop()
    if list(df.columns) != COLUMNAS_ESPERADAS:
        st.error("Las columnas del archivo no coinciden con las esperadas.")
        st.stop()
        
    st.success("Archivo validado correctamente.")
    
    # 2. Visualización Gráfica Interactiva
    st.markdown("### 📊 Gráficos del Turno")
    analito_sel = st.selectbox("Selecciona un analito numérico para visualizar:", ANALITOS_NUMERICOS)
    fig_line = px.line(df, x="Hora_Muestreo", y=f"{analito_sel}_Valor", title=f"Comportamiento de {analito_sel}")
    fig_line.add_hline(y=df[f"{analito_sel}_LS"].iloc[0], line_dash="dash", line_color="red", annotation_text="Límite Sup")
    fig_line.add_hline(y=df[f"{analito_sel}_LI"].iloc[0], line_dash="dash", line_color="red", annotation_text="Límite Inf")
    st.plotly_chart(fig_line, use_container_width=True)
    
    # 3. Preparación de Datos
    resumen_texto = generar_pre_resumen(df)
    imagen_consolidada = generar_imagen_matplotlib(df)
    
    # 4. Flujo de Correo
    st.markdown("### ✉️ Notificación por Correo")
    cc_email = st.text_input("Ingresa un correo de copia (CC) obligatorio para enviar:")
    
    if "borrador" not in st.session_state:
        st.session_state.borrador = None

    if st.button("Generar Borrador de Correo"):
        if not validar_correo(cc_email): # CORRECCIÓN APLICADA AQUÍ
            st.warning("Debes ingresar un correo electrónico válido para la copia.")
        else:
            with st.spinner("La IA está redactando el borrador..."):
                borrador = redactar_correo_ia(resumen_texto)
                if borrador:
                    st.session_state.borrador = borrador
                    st.success("Borrador generado con éxito. Revisa abajo y envía.")
    
    if st.session_state.borrador:
        st.markdown("#### Vista Previa del Correo")
        # Separar asunto y cuerpo
        partes = st.session_state.borrador.split("\n", 1)
        asunto = partes[0] if len(partes) > 0 else "Asunto: Reporte de Calidad"
        cuerpo = partes[1] if len(partes) > 1 else st.session_state.borrador
        
        st.write(f"**{asunto}**")
        st.components.v1.html(cuerpo, height=400, scrolling=True)
        
        if st.button("Confirmar y Enviar Correo al Supervisor"):
            with st.spinner("Enviando correo vía SMTP..."):
                if enviar_correo(asunto, cuerpo, imagen_consolidada, cc_email):
                    st.success("¡Correo enviado correctamente al supervisor y a la copia!")
                    st.session_state.borrador = None # Limpiar tras enviar

    # 5. Asistente IA (Chat)
    st.markdown("---")
    st.markdown("### 🤖 Asistente Consultor de Calidad")
    st.write("¿Tienes dudas sobre los resultados? Pregunta al asistente técnico.")
    
    if "mensajes" not in st.session_state:
        st.session_state.mensajes = []

    for msg in st.session_state.mensajes:
        with st.chat_message(msg["rol"]):
            st.markdown(msg["contenido"])

    pregunta = st.chat_input("Ej: ¿Por qué falló el Grado Brix en la Línea 1?")
    
    if pregunta:
        # Mostrar pregunta del usuario
        st.session_state.mensajes.append({"rol": "user", "contenido": pregunta})
        with st.chat_message("user"):
            st.markdown(pregunta)
            
        # Llamar a Gemini (Agente 2)
        instrucciones_agente2 = f"""Eres un Ingeniero de Calidad Senior experto en envasado de gaseosas.
        Contexto actual del laboratorio: {resumen_texto}
        Responde la duda del usuario de forma directa y técnica. Estás autorizado a dar sugerencias operativas."""
        
        try:
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
            response = client.models.generate_content(
                model=MODELO,
                contents=pregunta,
                config=types.GenerateContentConfig(
                    temperature=0.6,
                    system_instruction=instrucciones_agente2
                )
            )
            respuesta_ia = response.text
            st.session_state.mensajes.append({"rol": "assistant", "contenido": respuesta_ia})
            with st.chat_message("assistant"):
                st.markdown(respuesta_ia)
        except Exception as e:
            st.error(f"Error en el chat: {e}")
