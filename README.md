# Selector TFM: prototipo 0.1

Primera implementacion funcional del selector multicriterio de Echeverry y Torres.
No es un sistema productivo ni constituye evidencia experimental del TFM.

Repositorio: https://github.com/maite828/genai-model-selector

## Inicio

Desde esta carpeta, con Python 3.11 o posterior y Node.js:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock
npm ci
npm run build
.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8765
```

Abrir http://127.0.0.1:8765. No exponer el servidor a una red publica.
Si el puerto esta ocupado, elegir otro con `--port` y abrir ese mismo puerto.
`requirements.lock` fija todas las versiones del entorno verificado;
`requirements.txt` enumera las dependencias directas.

## Implementado

- FastAPI, flujo determinista LangGraph y frontend local sin servicios externos.
- Tres candidatos abstractos; cuatro perfiles WSM del documento del TFM.
- Privacidad, coste estimado y calidad de referencia como filtros previos.
- Abstencion si no quedan candidatos. Desempate por coste y luego identificador.
- Normalizacion min-max sobre los tres modelos del catalogo completo por tarea.
- Comparacion, traza, historial SQLite y exportacion JSON.
- Estados separados para seleccion, abstencion, ejecucion completada, bloqueada y fallida.
- Adaptador Ollama para ejecucion local, sin descargas automaticas.
- Token de sesion para escrituras, validacion del Host y contenido no persistido.

## Datos de demostracion

Todos los valores de calidad, coste y emisiones son inventados para probar
el flujo. No pertenecen a modelos comerciales o abiertos reales. Las etiquetas
local-small, local-large y remote describen roles, no resultados medidos.
Las tasas sinteticas de coste incluyen un coste local no nulo; no representan
una tarifa verificada. Se multiplican por (entrada estimada + limite de salida)/1000.
La entrada se aproxima a un token por cuatro caracteres: no es tokenizacion real.
El filtro de presupuesto compara estimaciones, no garantiza gasto efectivo.
Los limites de normalizacion se conservan aunque se excluyan candidatos.

El analizador usa la tarea declarada y unas pocas expresiones locales para
senales sensibles. No es un clasificador entrenado, DLP ni garantia juridica.
Los datos internos/sensibles siempre excluyen remotos. En esta version no se
envian solicitudes a proveedores remotos, incluso si su candidato resulta ganador.

## Vinculacion local opcional

En el equipo del piloto, con Ollama activo y los modelos ya instalados:

```sh
.venv/bin/python run_local.py
```

Este arranque vincula `local-small` a `llama3.2:latest` (3B) y `local-large`
a `qwen2.5:latest` (7B), sin descargar nada. Las variables de entorno explicitas
tienen prioridad. Detener antes cualquier servidor que ocupe el puerto 8765.
El contexto de ejecucion es de 4096 tokens; el modelo permanece cargado hasta
dos minutos tras la respuesta. El historial conserva su digest para identificar
la version efectiva, ya que la etiqueta `latest` puede cambiar.

Con Ollama activo y modelos ya instalados, establecer nombres exactos antes de
arrancar el servidor:

```sh
TFM_LOCAL_SMALL='nombre-local-compacto' TFM_LOCAL_LARGE='nombre-local-avanzado' .venv/bin/uvicorn app:app --host 127.0.0.1 --port 8765
```

El boton de ejecucion requiere confirmacion. El servidor recalcula la decision
y verifica que el destino existe localmente. Bloquea los metadatos remote_host,
remote_model y los nombres cloud; no reintenta con proveedores externos.
La vinculacion NO convierte las metricas sinteticas en mediciones del modelo.
Se registran latencia y tokens si Ollama los devuelve; no energia.
La integracion real requiere prueba en el hardware del grupo. Las pruebas
automatizadas del adaptador utilizan respuestas simuladas.

## Privacidad y trazabilidad

No se persisten prompts ni respuestas. SQLite conserva metadatos: fecha, tarea,
politica de privacidad, presencia de senales sensibles, estimacion de longitud,
pesos, restricciones, candidatos y decision. Se pueden borrar desde Decisiones.
No hay telemetria de LangSmith activada. No se utilizan fuentes, imagenes o APIs
externas desde la interfaz. Los datos estan en data/decisions.sqlite.
No utilizar datos personales reales durante esta fase de desarrollo.

## Pruebas

Compilar primero la interfaz con `npm ci` y `npm run build` en una copia nueva.

```sh
.venv/bin/python -m unittest -v
```

## Trabajo en equipo

Clonar el repositorio y seguir los pasos de inicio. Trabajar en una rama por
cambio y revisar mediante pull request antes de integrar en `main`. No incluir
credenciales, datos personales, bases de datos locales ni resultados sinteticos
como si fueran mediciones. La licencia MIT original del repositorio se conserva.

## Pendiente para el TFM

El [piloto de veinte casos](evaluation/pilot/README.md) incluye enunciados,
criterios esperados, pruebas de referencia de codigo, rubrica de doble
evaluacion y ficha de valoracion. Su ejecutor captura 40 respuestas locales y
prepara paquetes anonimizados; las puntuaciones requieren revision humana.

1. Acordar hardware y modelos concretos y caracterizar su rendimiento.
2. Sustituir el catalogo sintetico por uno medido, versionado y congelado.
3. Definir politicas y conectar el proveedor remoto con consentimiento explicito.
4. Instrumentar energia, incertidumbre y costes, incluida la sobrecarga.
5. Desarrollar y justificar decisiones agenticas, recuperacion y validacion de salidas.
6. Ejecutar piloto, baselines y evaluacion final con particiones independientes.

## Fuentes tecnicas

- FastAPI: https://fastapi.tiangolo.com/tutorial/first-steps/
- LangGraph: https://docs.langchain.com/oss/python/langgraph/graph-api
- Ollama: https://docs.ollama.com/api/generate

Estas fuentes documentan las integraciones, no respaldan los valores sinteticos.
