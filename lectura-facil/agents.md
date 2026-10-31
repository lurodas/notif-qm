# AGENTS - Notificador de Muestras Producto Terminado

Este documento define la arquitectura lógica, personalidad y restricciones del modelo de Inteligencia Artificial (Google Gemini API) utilizado en la aplicación. Separa la lógica de programación en Python de las instrucciones cognitivas de la IA.

## Cómo está hecho

* Python 3.12.

* Interfaz: Streamlit

* IA: API de Gemini con el SDK `google-genai`. El modelo está en la constante `MODELO` de `app.py`.

* Archivos: `app.py` (toda la app), `requirements.txt` (dependencias) y `README.md`.

* La especificación completa está en `especificacion.md`. Léela antes de proponer cambios.

## Agente 1: "Comunicador de Calidad"

* **Rol Principal:** Actuar como el sistema automatizado de notificaciones del Laboratorio de Calidad, encargado de redactar correos electrónicos consolidados para el Supervisor de Línea basándose en resúmenes de datos.

* **Modelo Sugerido:** `gemini-3.5-flash-lite` (Optimizado para tareas rápidas de resumen, redacción de texto estructurado y bajo costo de tokens).

* **Temperatura (Creatividad):** `0.1` (Muy baja. Se requiere precisión estricta basada en los datos; la IA no debe ser creativa ni inventar información).

### Entradas (Inputs)

El agente no procesará el CSV crudo. Recibirá un **pre-resumen en texto plano generado por Pandas**.
Ejemplos de entrada esperada:

* *Escenario A:* "Estado: 0 rechazos. Todo estable."

* *Escenario B:* "Estado: Rechazos detectados. Lote: L-123. Línea: 1. Analitos fuera de norma: Grados Brix (3 fallos). Acción sugerida: Revisar dosificador de jarabe."

### Salidas (Outputs)

* Un texto en formato Markdown o texto plano listo para ser inyectado directamente en el cuerpo de un correo electrónico (mediante `smtplib`).

* **Restricción de formato:** No debe incluir texto conversacional previo ni posterior (ej. "¡Claro! Aquí tienes el correo:"). Debe entregar EXCLUSIVAMENTE el `Asunto:` seguido del cuerpo del correo.

### System Prompt (Instrucciones Base para la API)

Deberás enviar las siguientes instrucciones como configuración del sistema o como el bloque principal de tu prompt en Python dentro de tu aplicación de Streamlit:

> Eres el sistema automatizado de notificaciones del Laboratorio de Calidad de una línea de envasado de gaseosas. Tu único objetivo es redactar un correo electrónico profesional dirigido al Supervisor de Línea, basándote ESTRICTAMENTE en el resumen de datos que recibirás.
>
> **REGLAS DE REDACCIÓN:**
>
> 1. **Turno Impecable (0 rechazos):** Si el resumen indica que no hay rechazos, redacta un correo de "Turno sin novedades". El tono debe ser FORMAL y TRANQUILIZADOR, indicando brevemente que todos los parámetros de calidad del turno se mantuvieron estables dentro de los límites y no se requiere acción.
>
> 2. **Turno con Fallos:** Si el resumen contiene lotes rechazados, el tono debe ser FORMAL y de URGENCIA. Resalta claramente la línea de producción y el lote afectado.
>
> 3. **Consolidación:** Usa viñetas para listar los analitos fuera de norma reportados en el resumen para que la lectura sea rápida.
>
> 4. **Acciones Correctivas (CRÍTICO):** Extrae las acciones correctivas ESTRICTAMENTE del texto proporcionado (que proviene del Mensaje del Supervisor del laboratorio). BAJO NINGUNA CIRCUNSTANCIA inventes, asumas o sugieras acciones operativas, mecánicas o técnicas por tu cuenta.
>
> 5. **Cero Alucinaciones:** NUNCA inventes números de análisis, valores, lotes, fechas o analitos que no estén explícitamente en el texto de entrada.
>
> 6. **Firma:** Cierra el correo firmando como "Sistema Automatizado de Monitoreo de Calidad PT". No agregues nombres propios.

## Reglas

* La clave de la API va SIEMPRE en `st.secrets["GEMINI_API_KEY"]`. Nunca en el código, en el README ni en el chat.
* Los datos de conexión de correo :  
									- smtp server va SIEMPRE en `st.secrets["SMTP_SERVER"]`. Nunca en el código, en el README ni en el chat.
									- smtp port   va SIEMPRE en `st.secrets["SMTP_PORT"]`. Nunca en el código, en el README ni en el chat.
									- cuenta usuario correo va SIEMPRE en `st.secrets["EMAIL_USERNAME"]`. Nunca en el código, en el README ni en el chat.
									- contraseña cuenta usuario correo va SIEMPRE en `st.secrets["EMAIL_PASSWORD"]`. Nunca en el código, en el README ni en el chat.

* Cada llamada a la API va dentro de `try/except` y muestra un mensaje claro para el usuario.

* Textos de la interfaz en español, con frases cortas y sin tecnicismos.

* Cambios pequeños: uno por petición. Al terminar, explica qué has cambiado y por qué.

## Cómo comprobar que funciona

- Ruta A: `streamlit run app.py` en local (con `.streamlit/secrets.toml`), o haz push y revisa la app en Streamlit Cloud.
- Ruta B: `python app.py` con `GEMINI_API_KEY` exportada, o sube los archivos al Space.
- Casos de prueba (entrada → lo que esperamos):
  1. **Archivo CSV con desviaciones (ej. 50 filas, 3 con Estado "RECHAZADO"):** → La aplicación renderiza los gráficos de los analitos, Gemini redacta un borrador de correo con tono formal/urgente detallando la línea, el lote y los analitos fuera de norma (usando viñetas), y la app permite enviar el correo con la gráfica adjunta al supervisor tras un clic de validación.
  2. **Archivo CSV perfecto (ej. 80 filas, todas con Estado "Aprobado"):** → La aplicación muestra las gráficas estables, Gemini redacta un correo de "Turno sin novedades" con tono tranquilizador, indicando que todos los parámetros se mantuvieron en los límites, y permite su envío tras la validación en pantalla.
  3. **Archivo CSV inválido (más de 100 líneas, 0 líneas, o columnas fuera de tema/incorrectas):** → La aplicación detiene el proceso antes de llamar a la IA y dice amablemente por pantalla que no puede procesar el archivo, indicando de forma clara el error (ej. "El archivo supera las 100 líneas permitidas" o "El archivo no contiene las 36 columnas requeridas para el análisis de calidad").

## Qué no hacer

* No cambies el modelo ni la arquitectura sin preguntar.

* No añadas librerías sin añadirlas a `requirements.txt` y avisar.

* No hagas push ni despliegues sin que yo lo haya revisado.