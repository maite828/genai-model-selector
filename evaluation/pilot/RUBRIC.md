# Rubrica propuesta del piloto v1

Esta rubrica es un instrumento original para el piloto del TFM. Los pesos y
umbrales son decisiones metodologicas propuestas, no una escala validada.
Los dos integrantes deben leerla y resolver dudas antes de generar las respuestas.

## Puntuacion de cada respuesta

Cada evaluador asigna cuatro puntuaciones enteras entre 0 y 3 y aporta evidencia
de la respuesta para justificar las penalizaciones. No se muestra el modelo,
su velocidad ni su puntuacion WSM mientras se evalua el contenido.

| Dimension | Peso | 0 | 1 | 2 | 3 |
|---|---:|---|---|---|---|
| Correccion y fidelidad | 50 % | Resultado central erroneo, contradiccion central o invencion decisiva | Error importante en alguna afirmacion o parte funcional | Solo imprecision menor que no cambia la conclusion | Afirmaciones y resultado correctos y fieles al material |
| Cobertura | 25 % | Ninguno de los tres puntos esperados cubierto | Un punto esperado cubierto | Dos puntos esperados cubiertos | Los tres puntos esperados cubiertos |
| Cumplimiento de instrucciones | 15 % | Incumple todas las comprobaciones de formato | Cumple algunas, menos de la mitad | Cumple al menos la mitad, pero no todas | Cumple todas las comprobaciones |
| Claridad | 10 % | No se puede interpretar | Ambiguedad o desorganizacion que dificulta entender el resultado | Comprensible con alguna redundancia o ambiguedad menor | Directa, organizada y sin ambiguedades relevantes |

Puntuacion normalizada:

`Q = (0.50 * correccion + 0.25 * cobertura + 0.15 * instrucciones + 0.10 * claridad) / 3`

Guardar las puntuaciones originales y Q sin redondear; mostrar tres decimales.
Esta Q evalua una respuesta. No es la puntuacion WSM del selector ni una medida
de energia. Los pesos de esta rubrica son independientes de los perfiles WSM.

Reglas de aplicacion:

- Cobertura cuenta cada elemento de `expected_points` solo si todas sus partes
  estan presentes de forma correcta; no basta con mencionar el asunto.
- En formato, comprobar cada elemento de `format_checks` por separado. Si solo
  hay una comprobacion, su resultado es 0 o 3; no forzar valores intermedios.
- Contar palabras separando por espacios; numeros cuentan como palabras y los
  marcadores de lista aislados no cuentan. En W01 se incluye el asunto.
- Aceptar sinonimos, distinto orden y notacion numerica equivalente salvo que
  el enunciado imponga un orden o formato. No exigir coincidencia literal.
- En K04, analizar el JSON; el orden de claves no importa, claves extra si
  incumplen el formato. `null` no equivale al texto `"null"`.
- Cada error de `critical_errors` se marca individualmente con evidencia.
  Informar siempre de la proporcion de respuestas sin errores criticos junto
  con Q. Un Q alto no convierte una respuesta con error critico en aceptable.
- La omision de un dato esperado baja cobertura; una afirmacion que contradice
  el material baja correccion. Si ocurren ambas, justificar ambas penalizaciones.
- En resumen y redaccion no penalizar estilo personal o una formulacion distinta
  si cumple el encargo. Ningun juez LLM sustituye a los evaluadores en este piloto.

## Reglas especificas para codigo

Los casos C01-C04 incluyen entradas y salidas en `code_tests`. Son pruebas
de referencia publicadas para los evaluadores, no parte del prompt del modelo.
Debe cumplirse tambien el contrato completo: nombre y firma, ausencia de
mutacion de la entrada y comportamiento descrito. Las pruebas no son exhaustivas.

Para correccion: 0 si no ejecuta o falla todas las pruebas; 1 si supera algunas
pero menos de la mitad; 2 si supera al menos la mitad pero no todas o incumple
otro requisito funcional; 3 si supera todas y cumple el contrato. Registrar
numero de pruebas superadas/total y cualquier requisito funcional incumplido.
Un resultado numerico flotante admite error absoluto de hasta 1e-9.

Un unico bloque Markdown puede extraerse para probar la funcion, pero implica
incumplimiento de "solo la funcion". No corregir ni completar el codigo generado.
No ejecutar codigo generado en el servidor del prototipo ni en la sesion del
evaluador: usar un entorno aislado sin red, credenciales o archivos personales,
con limites de tiempo y memoria. Este paquete no incluye ese ejecutor aislado;
si no esta disponible, dejar pruebas funcionales como pendientes y no darles
porcentaje de aprobacion.

## Fallos de generacion

Separar un fallo del servicio de una respuesta incorrecta. Registrar estados
`completed`, `timeout`, `error` o `empty`, y el motivo de terminacion si existe.
Una respuesta truncada por el limite de tokens conserva el estado y se evalua
tal como llego, anotando la truncacion. No repetir solo respuestas de baja calidad.

Para timeout/error/empty no asignar puntuaciones humanas ficticias. Registrar
Q como ausente, informar tasa de finalizacion y Q de respuestas evaluables por
separado. Como indicador secundario se puede calcular Q efectivo contando fallos
como cero, siempre identificado y con su denominador. Cada reintento ocupa una
fila nueva y no sustituye ni borra el intento original.

## Dos evaluadores

1. Luz Maite y Arturo revisan la rubrica y acuerdan una version antes de puntuar.
2. Cada uno puntua las 40 respuestas de forma independiente: 20 casos por dos
   modelos. Se ocultan nombre de modelo, tiempos y puntuaciones del otro evaluador.
3. Comparar las puntuaciones originales. Revisar cualquier desacuerdo en errores
   criticos, una diferencia de dos o mas niveles en una dimension, o |Q_A-Q_B| > 0.15.
4. Registrar el consenso y su motivo sin sobrescribir las dos valoraciones iniciales.
   Si no hay acuerdo, marcarlo como no resuelto y conservar ambas valoraciones.
5. Informar acuerdo exacto por dimension y media de |Q_A-Q_B| sobre pares completos,
   indicando cuantos hay. Son indicadores descriptivos, no prueba de validez.

Estos nombres identifican a los dos evaluadores propuestos, no asignan las Partes
A y B del desarrollo. Cuatro casos por familia no permiten conclusiones generales.
