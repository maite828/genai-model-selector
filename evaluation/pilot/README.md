# Piloto v1: veinte casos y criterios previos

Objetivo: comprobar la viabilidad del protocolo, descubrir problemas del selector
y ajustar la evaluacion antes de fijar el experimento final.

Material preparado para captura local y evaluacion humana independiente.
Las ejecuciones concretas se documentan en su manifest local; las puntuaciones
solo se incorporan tras la revision de los dos evaluadores.

- [Casos legibles](CASES.md): los veinte enunciados y sus criterios.
- [Casos estructurados](cases.json): fuente para un futuro ejecutor.
- [Rubrica](RUBRIC.md): escala, pesos y procedimiento de doble evaluacion.
- [Ficha de valoracion](REVIEW_TEMPLATE.md): registro de evidencia y puntuaciones.
- `prepare.py`: valida la estructura y genera el cuaderno legible; no llama modelos.
- `run_pilot.py`: captura las 40 respuestas y prepara paquetes de evaluacion separados.

## Composicion

| Familia | Identificadores | Casos |
|---|---|---:|
| Conocimiento | K01-K04 | 4 |
| Razonamiento | R01-R04 | 4 |
| Codigo | C01-C04 | 4 |
| Resumen | S01-S04 | 4 |
| Redaccion | W01-W04 | 4 |

Las cinco familias usan los nombres de tarea del prototipo. Las dificultades
son propuestas basicas/intermedias y aun no estan validadas. Los ejercicios
de conocimiento incluyen material de referencia para no depender de busquedas.
Los dominios se concentran en el proyecto y en tareas elementales; la prueba
final necesitara mayor diversidad. Los casos sensibles son totalmente ficticios.

## Dos comprobaciones distintas

**Calidad del contenido:** enviar cada prompt a cada modelo local, sin pasar
por el selector para decidir cual responde. Obtener 40 respuestas en total.
Enviar solamente `prompt`, no los criterios ni las soluciones. Mantener la
misma configuracion en ambos modelos. El filtro del selector no debe impedir
que se mida el modelo alternativo en este ensayo local.

**Politica de seleccion:** enviar cada caso al selector con su `task`, `privacy`
y `allow_remote`, perfil equilibrio, coste maximo sintetico 0.02 y calidad minima 0.
Esperado: remoto excluido siempre que los datos sean internos/sensibles o no
haya autorizacion. `allow_remote=true` en casos restringidos es intencional:
la restriccion debe prevalecer. No se ejecuta ningun proveedor remoto.
No fijar un ganador universal: los pesos y el catalogo determinan el ganador.

Repetir la seleccion con `max_cost=0`: con el catalogo sintetico v1 todos los
casos deben abstenerse. Guardar version del catalogo, exclusiones y resultado.
Esto prueba la logica del filtro, no el coste real del hardware. La comprobacion
de privacidad no es un criterio de calidad de las respuestas locales.

## Condiciones propuestas

- Modelos ya instalados: Llama 3.2 3B Q4_K_M y Qwen 2.5 7B Q4_K_M.
- Registrar los digest completos al principio y verificar que no cambian.
  `latest` por si solo no identifica una version reproducible.
- Ejecucion local secuencial, nube deshabilitada, un modelo en memoria cada vez.
- Contexto 4096, salida maxima 512 tokens, temperatura 0 y semilla 42.
  Anotar servidor Ollama, equipo, configuracion efectiva y fecha; una semilla
  fija no garantiza igualdad entre versiones o dispositivos.
- Antes de cada bloque, cargar el modelo con una solicitud auxiliar fuera de
  estos veinte casos. Registrar la carga por separado y excluir el calentamiento.
- Propuesta de orden alternado por bloques: casos 1-10 con Llama y luego Qwen;
  casos 11-20 con Qwen y luego Llama, usando el orden de `cases.json`. Descargar
  de memoria el modelo anterior al cambiar. Esto reduce cambios constantes;
  no elimina efectos de orden o temperatura del equipo.
- Una generacion por caso/modelo. No usar esta muestra para estimar variabilidad
  temporal. Registrar latencia total, carga, tiempo de generacion, tokens de
  entrada/salida, finalizacion y fallos. Repeticiones posteriores se etiquetan.
- Conservar las respuestas de este experimento en archivos locales excluidos
  de Git. El historial habitual de la app no guarda contenido y no basta para
  la evaluacion humana. Usar `data/pilot/<run_id>/` para estos archivos.
- Dar a cada respuesta un identificador aleatorio. Guardar la correspondencia
  modelo/identificador aparte y presentar los casos en orden mezclado a ambos
  evaluadores. Las familias y el enunciado si son visibles para poder corregir.

## Analisis y decisiones

Informar por modelo y familia: numero de casos, tasa de finalizacion, media de Q,
errores criticos y latencias individuales. No comparar tiempos totales sin
considerar longitud de salida y carga. No presentar ahorro, calidad o emisiones
como demostrados por este paquete. Coste y emisiones permanecen sinteticos.

Antes de ejecutar, los dos integrantes revisaran la rubrica. Registrar el commit
del conjunto y la rubrica junto a cada ejecucion. Si se modifica un enunciado o
criterio, crear v2 y conservar la asociacion de los resultados con v1.

Estos casos pertenecen exclusivamente al piloto. Si se utilizan para elegir
modelos, ajustar prompts, reglas o pesos, quedan excluidos de la prueba final.
Tampoco cuentan como la particion de caracterizacion ni como la de ajuste del
diseno experimental amplio. No trasladar medias de cuatro casos directamente
al catalogo definitivo: primero ampliar y separar esas particiones.

## Comprobar los materiales

Desde la raiz del repositorio:

```sh
python3 evaluation/pilot/prepare.py
```

## Ejecutar y distribuir

Con Ollama local activo, los dos modelos instalados y nube deshabilitada:

```sh
.venv/bin/python evaluation/pilot/run_pilot.py
```

Cada ejecucion crea una carpeta nueva `data/pilot/<run_id>/`, excluida de Git.
No descarga modelos. Comprueba sus digest al principio y al final de cada bloque.
Guarda cada intento inmediatamente y conserva fallos; ante un timeout se detiene
para evitar solapar solicitudes. Los paquetes de una ejecucion interrumpida
muestran su numero de respuestas y no deben presentarse como un piloto completo.

Dentro de cada carpeta:

- `evaluacion_Maite/` y `evaluacion_Arturo/`: cuaderno con respuestas, rubrica,
  respuestas JSON anonimizadas y CSV de puntuaciones inicialmente vacio.
- `RESTRINGIDO_correspondencia_modelos.json`: clave para identificar los modelos;
  no distribuir junto con las fichas ni abrir antes de completar las puntuaciones.
- `RESTRINGIDO_resultados.jsonl`: respuestas originales, identidad y tiempos.
- `manifest.json`: estado, recuentos, modelos, condiciones, calentamientos y hashes.
- `snapshot_*`: copia de materiales y ejecutor usados en ese ensayo.

Entregar a cada evaluador solamente su subcarpeta. Los mismos identificadores
anonimos permiten comparar las valoraciones, aunque el orden se mezcla de forma
independiente. Esta ocultacion administrativa no garantiza que el estilo de una
respuesta no sugiera su origen. El propietario de los archivos puede acceder a
la clave: es una separacion de materiales, no un control de acceso.

No se ejecuta codigo generado ni se asignan puntuaciones automaticamente.
En los casos de codigo, dejar las pruebas funcionales pendientes hasta contar
con un ejecutor aislado. Las respuestas de cualquier familia se conservan
exactamente como fueron generadas, incluidas las truncadas.

Pruebas del empaquetado (sin inferencia):

```sh
.venv/bin/python -m unittest discover -s evaluation/pilot -p 'test_*.py' -v
```

## Consolidar las valoraciones

Cada evaluador completa su `puntuaciones.csv` conservando identificadores y
columnas. Usar enteros 0-3 en las cuatro dimensiones. En `errores_criticos`
escribir `ninguno` si no hay errores, o `C1;C2` para los errores correspondientes
al orden de la lista del caso (C1 es el primero). No dejar una celda vacia para
significar cero o ausencia de errores. Las penalizaciones requieren evidencia.
En los casos de codigo, completar pruebas superadas y total solo despues de
ejecutarlas en un entorno aislado; mientras tanto quedan pendientes.

Guardar las fichas devueltas dentro de las respectivas subcarpetas del ensayo.
El consolidador admite CSV separado por comas o por punto y coma, en UTF-8.

```sh
.venv/bin/python evaluation/pilot/consolidate.py data/pilot/IDENTIFICADOR_DEL_ENSAYO
```

El informe comprueba las 80 valoraciones, identidad de las filas, rangos y
evidencia. Cada uso crea un informe fechado sin sobrescribir fichas o informes
anteriores. Mientras quede alguna valoracion pendiente, informa solo del avance.
Cuando ambos terminan, calcula Q y acuerdo entre evaluadores y senala los
desacuerdos previstos en la rubrica, conservando las dos notas originales.

El informe no lee la clave de modelos ni emite rankings por modelo. La media de
dos notas se etiqueta como media, no como consenso. La adjudicacion de desacuerdos
y la posterior comparacion de modelos son pasos separados. Los resultados no
se incorporan automaticamente al catalogo de seleccion.
