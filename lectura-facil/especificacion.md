# Especificación · [Notificador_Muestras_PT]
## Descripción
> Se requiere una aplicacion  en Python con Streamlite la cual debe leer el archivo csv (Generar error si supera las 100 lineas o si trae 0 lineas) y analizar su informacion usando la librería de análisis de datos Pandas de Python, utilizar Plotly para renderizar una gráfica interactiva en Streamlit por ejemplo, un gráfico que muestre el comportamiento de los analitos durante el turno, marcando en rojo los puntos que superaron el límites especificados (en la las variables cualitativas usa gráficos de barras con las frecuencias de fallos). Para aislar las filas del archivo CSV donde el Estado_Calidad es "RECHAZADO",  generar un correo enviado desde smtplib (Solicita las variables y almacenar en memoria sesion Streamlit, manejar errores de autenticación: smtp_server, smtp_port 465 fijo, remitente, password enmascarada, destinatario al momento de cargar el archivo) que alerte al supervisor de la linea con la API de Gemini, usando los datos de los lotes defectuosos, usar Matplotlib para generar una imagen que ira incluida en el correo como evidencia gráfica de los puntos que fallaron, se debe generar un solo documento/imagen consolidado que contenga la información por analito, linea de producción y fecha.

## 1. Problema y usuario

- **Quién tiene el problema:** [Supervisor linea de producción de envasado de producto terminado (Latas Gaseosas)]
- **Cómo lo resuelve hoy:** [En la actualidad es una operación manual revisar un archivo recibido via correo que contiene los resultados de laboratorio]
- **Qué le molesta de cómo lo hace hoy:** [La actividad manual genera una perdida de tiempo en localizar la información indicada]
- **Qué parte resuelve la IA:** [La IA debe revisar los resultados de laboratorio,determinar cuando se sale del rango de tolerancia el analisis y notificar via correo esos resultados]

## 2. Qué hace el producto

Máximo tres funcionalidades. Si hay más, van al apartado 8.

1. [Leer los resultados de laboratorio de un producto terminado envasado en la linea de producción]
2. [Determinar si hay algun parametro fuera de rango y si es asi la aplicación  redacta un correo dinámicamente por la API de Gemini y lo muestra al usuario si detecta el error (por si la IA alucina), la app primero genera un borrador en pantalla para validación y se despacha con el primer clic posterior.]
3. [El usuario recibe el correo automatizado con las graficas correspondientes]

## 3. Entradas y salidas


 [El usuario sube a la aplicación un archivo CSV con los resultados de analisis de laboratorio, la estructura del archivo que se sube es : Fecha_Analisis,	Hora_Muestreo,	Lote_Produccion,	Linea_Produccion,	Grados_Brix_LI,	Grados_Brix_Valor,	Grados_Brix_LS,	Volumenes_CO2_LI,	Volumenes_CO2_Valor,	Volumenes_CO2_LS,	pH_LI,	pH_Valor,	pH_LS,	Acidez_Titulable_LI,	Acidez_Titulable_Valor,	Acidez_Titulable_LS,	Volumen_Llenado_LI,	Volumen_Llenado_Valor,	Volumen_Llenado_LS,	Integridad_Cierre_Esperado,	Integridad_Cierre_Valor,	Presion_Interna_LI,	Presion_Interna_Valor,	Presion_Interna_LS,	Apariencia_Color_Esperado,	Apariencia_Color_Valor,	Sabor_Aroma_Esperado,	Sabor_Aroma_Valor,	Mohos_Levaduras_LI,	Mohos_Levaduras_Valor,	Mohos_Levaduras_LS,	Mesofilos_Aerobios_LI,	Mesofilos_Aerobios_Valor,	Mesofilos_Aerobios_LS,	Estado_Calidad,	Mensaje_Supervisor] |
 [La App lee el archivo y como los datos ya están perfectamente estructurados en un archivo CSV que incluye los límites exactos de cada analito, la forma más rápida, segura y económica de detectar las desviaciones es usar Pandas, la librería de análisis de datos de Python. El rol de la API de Gemini entra en la segunda fase, la comunicación. Una vez que el código en Python filtra y aísla únicamente las filas que presentan problemas de calidad, se le debe pasar esos datos específicos a Gemini mediante un prompt. La API tomará esa información tecnica y redactará automáticamente un correo electrónico (lista de correos separados por comas, se debe validar la lista de correos antes de intentar conectar con el servidor SMTP) profesional, claro y con sentido de urgencia para el supervisor, resumiendo qué lote falló, qué analitos están fuera de norma y qué acción correctiva sugiere el sistema a esa partida de producción.] | [Si la Producción es impecable :(0 rechazos) y el Estado_Calidad es "Aprobado" en el 100% de las filas, la API de Gemini redacte un correo de "Turno sin novedades", genera grafica demostrando que todo estuvo estable, se muestra por pantalla y se envia con el primer clic. Si el archivo contiene múltiples lotes defectuosos y docenas de desviaciones, Gemini debe consolidar todo en un único correo resumen] |


## 4. La pieza de IA

- **Opción elegida:** [API de Gemini]
- **Por qué:** [La libreria de Pandas con la ayuda de la API de Gemini dan una solución sencilla al problema planteado]
- **Instrucciones para el modelo (system prompt):** [Usar tono formal y urgente y la estructura debe seguir Gemini al redactar el mensaje es formal indicando la información completa con las desviaciones encontradas]

## 5. Flujo del usuario

1. [El usuario entra y carga el archivo]
2. [La aplicación despliega graficamente por pantalla la información del laboratorio y genera el correo de alerta, si es necesario]
3. [El supervisor recibe el correo , si hay alertas de desviaciones]

## 6. Restricciones

- Coste cero: capa gratuita de la API y despliegue gratuito (ruta A o B).
- La clave de la API va en secretos, nunca en el código.
- Sin datos personales reales.
- Lenguaje sencillo, para alguien sin conocimientos técnicos.
- [Otras restricciones de vuestro problema]

## 7. Criterios de aceptación

La app está bien si:

| Entrada | Resultado esperado |
|---|---|
| [caso normal] | [qué debe pasar] |
| [caso límite: texto vacío, pregunta fuera de tema…] | [qué debe pasar] |
| [error: se acaba la cuota] | [mensaje claro para el usuario] |
| [error: timeout] | [mensaje claro para el usuario] |
| [error: Si la API de Gemini falla permanentemente, la aplicación debe cancelar el envío del correo y deplegar al usuario el mensaje de error] |
| [error: Si la API de Gemini falla permanentemente, la aplicación debe cancelar el envío del correo y deplegar al usuario el mensaje de error] |
| [error: Corrupción de datos de entrada: Si el usuario sube un archivo con las 36 columnas requeridas, pero con tipos de datos incorrectos o vacios, se debe generar un mensaje de error] |
| [error: Corrupción de datos de entrada: Si el archivo subido no contiene exactamente las 36 columnas esperadas debe generar un mensaje de error] |


## 8. Fuera de alcance (por ahora)

- [Ideas que dejáis para después]

## 9. Despliegue

- **Ruta:** [A (Streamlit Community Cloud)]
- **Si trabajáis en equipo (opcional):** []