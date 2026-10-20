import streamlit as st
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

st.set_page_config(page_title="Envío de Análisis por Correo", layout="wide")

st.title("📋 Notificador de Archivos de Análisis")
st.write("Sube un archivo CSV con las columnas correspondientes para enviar una notificación automática a **lurodas@gmail.com**.")

# --- Configuración lateral para SMTP ---
st.sidebar.header("Configuración del Servidor de Correo (Emisor)")
sender_email = st.sidebar.text_input("Tu correo electrónico (Emisor)", placeholder="ejemplo@gmail.com")
sender_password = st.sidebar.text_input("Tu contraseña o clave de aplicación", type="password")
smtp_server = st.sidebar.text_input("Servidor SMTP", value="smtp.gmail.com")
smtp_port = st.sidebar.number_input("Puerto SMTP", value=587)

destinatario = "lurodas@gmail.com"

uploaded_file = st.file_uploader("Sube tu archivo CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # Carga del CSV
        df = pd.read_csv(uploaded_file)
        
        # Limpieza de nombres de columnas
        df.columns = [col.strip() for col in df.columns]
        
        columnas_requeridas = [
            "Categoría",
            "Parámetro de Análisis",
            "Rango Aceptable / Especificación",
            "Unidad / Método"
        ]
        
        # Validar la estructura del archivo
        columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
        
        if not columnas_faltantes:
            st.success("Estructura del archivo CSV validada correctamente.")
            st.subheader("Vista previa de los datos:")
            st.dataframe(df, use_container_width=True)
            
            if st.button("📧 Enviar Notificación por Correo"):
                if not sender_email or not sender_password:
                    st.error("Por favor, configure las credenciales de correo (Emisor) en la barra lateral para poder realizar el envío.")
                else:
                    with st.spinner("Enviando correo..."):
                        try:
                            # Construcción del mensaje HTML
                            msg = MIMEMultipart()
                            msg["From"] = sender_email
                            msg["To"] = destinatario
                            msg["Subject"] = "Notificación de Parámetros de Análisis"
                            
                            tabla_html = df.to_html(index=False, border=1, classes="table table-striped")
                            
                            cuerpo_html = f"""
                            <html>
                              <body>
                                <p>Estimado destinatario,</p>
                                <p>Se han cargado nuevos parámetros de análisis en el sistema. A continuación se presentan los detalles:</p>
                                {tabla_html}
                                <br>
                                <p>Este es un correo automático.</p>
                              </body>
                            </html>
                            """
                            msg.attach(MIMEText(cuerpo_html, "html"))
                            
                            # Configurar conexión segura e inicio de sesión
                            server = smtplib.SMTP(smtp_server, smtp_port)
                            server.starttls()
                            server.login(sender_email, sender_password)
                            server.sendmail(sender_email, destinatario, msg.as_string())
                            server.quit()
                            
                            st.success(f"¡La información ha sido enviada exitosamente a {destinatario}!")
                        except Exception as e:
                            st.error(f"Ocurrió un error al enviar el correo: {e}")
        else:
            st.error(f"El archivo no contiene el formato esperado. Faltan las siguientes columnas: {', '.join(columnas_faltantes)}")
            st.info(f"Asegúrate de que tu archivo contenga exactamente estas columnas: {', '.join(columnas_requeridas)}")
            
    except Exception as e:
        st.error(f"No se pudo procesar el archivo CSV: {e}")
