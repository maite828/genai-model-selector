# Piloto v1: veinte casos y criterios previos

Objetivo: comprobar la viabilidad del protocolo, descubrir problemas del selector
y ajustar la evaluacion antes de fijar el experimento final.

Material preparado, aun sin ejecutar ni puntuar este conjunto.

- [Casos legibles](CASES.md): los veinte enunciados y sus criterios.
- [Casos estructurados](cases.json): fuente para un futuro ejecutor.
- [Rubrica](RUBRIC.md): escala, pesos y procedimiento de doble evaluacion.
- [Ficha de valoracion](REVIEW_TEMPLATE.md): registro de evidencia y puntuaciones.
- `prepare.py`: valida la estructura y genera el cuaderno legible; no llama modelos.

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

El siguiente trabajo es implementar la captura local de las 40 respuestas y
la preparacion de paquetes anonimizados para evaluacion. Este paquete define
los materiales previos y no afirma que esas ejecuciones ya se hayan realizado.
