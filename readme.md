# Notificador de Muestras Producto Terminado (PT)

**Enlace a la app:** [https://notif-qm-kwdyp5yxi9jo9cnoykrxhj.streamlit.app/]
**Autor/a:** [LUIS ALBERTO RODAS CARRASCO]

## Pitch

Los supervisores de líneas de envasado de bebidas pierden tiempo valioso analizando manualmente extensos reportes de laboratorio para encontrar fallos. Esta aplicación automatiza la lectura de resultados, visualiza las tendencias en tiempo real y redacta alertas inmediatas. La IA de Gemini aporta valor dual: por un lado, traduce datos técnicos aburridos en correos corporativos urgentes; por otro, actúa como un ingeniero consultor que sugiere soluciones operativas. Aprendimos que limitar estrictamente a la IA (pasándole un resumen de Pandas en lugar del CSV completo) elimina a cero las alucinaciones numéricas. Como siguiente paso, integraríamos la aplicación directamente con los PLC de las máquinas para eliminar la dependencia de subir archivos manuales.

## El problema

El supervisor de la línea de envasado (latas de gaseosas) recibe actualmente un archivo con resultados de laboratorio que debe revisar a mano para detectar desviaciones en la calidad. Esta revisión manual genera una pérdida de tiempo crítica en localizar la información indicada, retrasando las acciones correctivas. Resolver esto de forma automatizada es vital, ya que detectar a tiempo un parámetro fuera de rango (como un pH bajo o mal sellado) evita el desperdicio o reproceso de cientos de litros de producto.

## Qué hace la app

1. **Carga y Validación:** El usuario sube un CSV con los análisis (la app valida que tenga las 36 columnas requeridas y no exceda 100 líneas).
2. **Visualización Interactiva:** Despliega gráficos interactivos (Plotly) para ver el comportamiento de los analitos durante el turno.
3. **Notificación Inteligente:** Si hay parámetros fuera de rango, la app genera un borrador de correo con gráficas adjuntas (Matplotlib) y permite despacharlo vía SMTP con un clic.
4. **Asesoría Técnica (Chat):** Permite al usuario conversar con un asistente de IA integrado para resolver dudas sobre los resultados y obtener recomendaciones de mantenimiento o ajustes.

## La pieza de IA

- **Qué usa:** API de Google Gemini con el modelo `gemini-3.5-flash-lite`, usando el SDK moderno `google-genai`.
- **Por qué esa opción:** Es un modelo extremadamente rápido, de bajo costo y altamente capaz tanto para tareas deterministas (redactar el correo sin inventar datos, Agente 1) como para tareas de razonamiento consultivo (chat técnico, Agente 2).
- **Qué pasa si falla:** La app cuenta con manejo de errores `try/except`. Si la API agota su cuota, falla la conexión o el servidor SMTP no responde, la aplicación detiene el envío, mantiene la interfaz gráfica funcionando (ya que depende de Pandas/Plotly) y muestra un mensaje de alerta amigable al usuario.

## Cómo la he construido

- **Herramientas:** Python 3.12, Streamlit, Pandas, Plotly, Matplotlib y asistencia de IA (Gemini para el código inicial y estructuración de prompts).
- **Fichero de contexto del agente:** [https://github.com/lurodas/notif-qm/blob/main/agents.md](AGENTS.md)
- **Prompts clave:**
  1. *Prompt Agente 1 (Correos):* "Eres el sistema automatizado de notificaciones del Laboratorio... Extrae las acciones correctivas ESTRICTAMENTE del texto proporcionado. BAJO NINGUNA CIRCUNSTANCIA inventes o sugieras acciones operativas por tu cuenta. Cero alucinaciones."
  2. *Prompt Agente 2 (Chat):* "Eres un Ingeniero de Calidad Senior experto en envasado de bebidas gaseosas... TÚ SÍ ESTÁS AUTORIZADO a sugerir soluciones técnicas basadas en tu experiencia industrial (ej. sugerir recalibrar válvulas, revisar presiones)."
  3. *Regla de Contexto:* "El agente no procesará el CSV crudo. Recibirá un pre-resumen en texto plano generado por Pandas."
- **Qué delegué al agente y qué revisé a mano:** Delegué a la IA la tarea de darle formato humano a los correos, consolidar la información y responder dudas técnicas generales en el chat. Revisé a mano (y obligué a que se hiciera con código puro de Python/Pandas) la validación de archivos, el conteo de errores y la detección de límites (LS/LI), para garantizar precisión matemática absoluta.

## Prueba y mejora

| Quién la probó | Qué probó | Qué pasó | Qué cambié |
|---|---|---|---|
| Yo como desarrollador | Archivo CSV vacío o con columnas incorrectas | La IA intentaba leerlo y generaba un error crudo en pantalla. | Añadí validaciones estrictas al inicio de `app.py` para verificar `len(df)` y las columnas exactas antes de llamar a la IA. |
| Yo como desarrollador | El costo/consumo de tokens al subir el CSV | Enviar las 36 columnas a Gemini consumía muchos tokens y confundía a la IA. | Implementé una función `generar_pre_resumen` con Pandas que extrae solo las anomalías y le pasa a la IA un texto de 3 líneas. |

## Ejecutar en local

```bash
pip install -r requirements.txt
```
**Ruta Principal:** Crea el archivo de secretos en `.streamlit/secrets.toml` con las claves (ver `AGENTS.md`) y ejecuta:
```bash
streamlit run app.py
```

## Capturas

*(Añade aquí las imágenes de tu aplicación)*
- `[Captura de pantalla: Gráficos de Plotly renderizados]`
- `[Captura de pantalla: Borrador de correo generado]`
- `[Captura de pantalla: Interacción con el Asistente IA en el chat]`
- `[Captura de pantalla: Mensaje de error amigable al subir un CSV inválido]`