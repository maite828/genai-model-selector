# Cuaderno de casos del piloto v1

Generado desde `cases.json`. Contiene criterios reservados a los evaluadores.
Al modelo se envia exclusivamente el texto del enunciado.

## K01: Memoria y almacenamiento

Familia: knowledge | Dificultad propuesta: basic | Privacidad: public | Autorizacion remota: True

### Enunciado

Ficha de referencia: La RAM mantiene datos de trabajo mientras el equipo funciona; su contenido se pierde al apagarlo. El SSD conserva archivos sin alimentacion. Un equipo tiene 16 GB de RAM y 512 GB de SSD. Responde en tres puntos, usando solo la ficha: 1) que recurso conserva los archivos al apagar; 2) que capacidad corresponde a la memoria de trabajo; 3) si ampliar el SSD aumenta por si solo la RAM.

### Puntos esperados

- El SSD conserva los archivos
- La memoria de trabajo es de 16 GB
- Ampliar el SSD no aumenta la RAM

### Errores criticos

- Confundir persistencia de RAM y SSD
- Afirmar que ampliar el SSD aumenta la RAM

### Formato

- Exactamente tres puntos
- Sin informacion externa

## K02: Alcance de una medida

Familia: knowledge | Dificultad propuesta: intermediate | Privacidad: public | Autorizacion remota: True

### Enunciado

Ficha de referencia: El tiempo de carga mide la preparacion del modelo. La latencia total abarca desde el envio de una solicitud hasta la respuesta completa, incluida la carga si la hay. Tokens por segundo mide la generacion, no la exactitud. En una prueba se anotan 5 segundos de carga, 12 segundos totales y 20 tokens por segundo. En tres frases explica que significa cada cifra y si permiten concluir que la respuesta es correcta.

### Puntos esperados

- 5 s corresponden a la preparacion
- 12 s son el tiempo total e incluyen la carga en esta prueba
- 20 tokens/s es velocidad de generacion y no demuestra correccion

### Errores criticos

- Sumar 5 y 12 como latencia total
- Inferir calidad por la velocidad

### Formato

- Tres frases
- Explica las tres cifras y la limitacion

## K03: Politica interna cerrada

Familia: knowledge | Dificultad propuesta: basic | Privacidad: internal | Autorizacion remota: True

### Enunciado

Manual ficticio interno: las solicitudes publicas pueden usar modelos locales o remotos si existe autorizacion. Las solicitudes internas o sensibles solo pueden usar modelos locales. La calidad no anula esta regla. Responde en dos puntos: que destinos admite una solicitud interna aunque se autorice el uso remoto, y si una mayor calidad del remoto cambia la decision.

### Puntos esperados

- La solicitud interna solo admite destinos locales
- La autorizacion remota no supera la restriccion interna
- Una mayor calidad remota no cambia esa restriccion

### Errores criticos

- Permitir el remoto para una solicitud interna

### Formato

- Dos puntos
- Aplicar solo el manual ficticio

## K04: Reconocer un dato ausente

Familia: knowledge | Dificultad propuesta: intermediate | Privacidad: public | Autorizacion remota: False

### Enunciado

Ficha ficticia del modelo Delta: contexto de 4096 tokens, ejecucion local, latencia observada de 4 segundos. No hay mas informacion. Contesta con las claves energia_kwh, calidad_evaluada y latencia_segundos en un objeto JSON sin texto adicional. Usa null si la ficha no aporta el dato; no estimes ni completes los valores ausentes.

### Puntos esperados

- energia_kwh es null
- calidad_evaluada es null
- latencia_segundos es 4

### Errores criticos

- Inventar energia o calidad

### Formato

- Objeto JSON valido
- Exactamente las tres claves solicitadas
- Sin texto adicional

### Objeto esperado

```json
{
  "energia_kwh": null,
  "calidad_evaluada": null,
  "latencia_segundos": 4
}
```

## R01: Presupuesto aritmetico

Familia: reasoning | Dificultad propuesta: basic | Privacidad: public | Autorizacion remota: True

### Enunciado

En un escenario ficticio cada solicitud cuesta exactamente 0,004 euros y el presupuesto es 0,020 euros. No hay otros costes. Indica el numero maximo entero de solicitudes completas, el coste de seis solicitudes y si seis caben en el presupuesto. Muestra una operacion breve para justificarlo.

### Puntos esperados

- Caben cinco solicitudes
- Seis cuestan 0,024 euros
- Seis exceden el presupuesto

### Errores criticos

- Admitir seis solicitudes
- Error en los resultados numericos

### Formato

- Incluye al menos una operacion
- Responde las tres cuestiones

## R02: Dependencias temporales

Familia: reasoning | Dificultad propuesta: intermediate | Privacidad: public | Autorizacion remota: False

### Enunciado

Una tarea A dura 2 horas. B dura 3 horas y empieza al terminar A. C dura 4 horas y tambien empieza al terminar A. B y C pueden ejecutarse en paralelo sin limitaciones de recursos. D dura 1 hora y empieza cuando terminan B y C. Todas las tareas empiezan lo antes posible. Calcula el tiempo total minimo e indica la cadena que lo determina. Explica la operacion en no mas de 80 palabras.

### Puntos esperados

- Tiempo total minimo de siete horas
- La cadena determinante es A-C-D
- Se usa 2 + max(3,4) + 1

### Errores criticos

- Sumar B y C como si fueran secuenciales
- Dar una duracion distinta de siete horas

### Formato

- Como maximo 80 palabras
- Justificacion breve

## R03: Restricciones antes de preferencias

Familia: reasoning | Dificultad propuesta: intermediate | Privacidad: sensitive | Autorizacion remota: True

### Enunciado

Ejercicio ficticio, sin datos reales. Una solicitud sensible solo puede usar modelos locales. Su presupuesto maximo es 0,005 euros. A es local, cuesta 0,004 y tiene calidad 0,75. B es remoto, cuesta 0,002 y tiene calidad 0,95. C es local, cuesta 0,006 y tiene calidad 0,90. Indica que candidato es admisible y explica por que se excluye cada uno de los otros. Usa tres puntos.

### Puntos esperados

- A es el unico admisible
- B se excluye por privacidad aunque sea mejor y mas barato
- C se excluye por superar el presupuesto

### Errores criticos

- Elegir B o C
- Tratar la privacidad como una preferencia compensable

### Formato

- Tres puntos
- Una justificacion por candidato

## R04: Abstencion justificada

Familia: reasoning | Dificultad propuesta: intermediate | Privacidad: internal | Autorizacion remota: False

### Enunciado

Ejercicio ficticio: una solicitud interna exige un modelo local y calidad minima 0,90. A es local con calidad 0,80; B es local con calidad 0,85; C es remoto con calidad 0,97. Ninguna otra regla permite excepciones. Indica la decision y explica en un parrafo breve por que elegir el candidato con mayor calidad no resuelve el problema.

### Puntos esperados

- El sistema debe abstenerse
- A y B no alcanzan el umbral
- C incumple la exigencia local

### Errores criticos

- Elegir cualquier candidato
- Rebajar una restriccion sin autorizacion

### Formato

- Un parrafo breve
- Explica por que C no resuelve el problema

## C01: Eliminar duplicados

Familia: code | Dificultad propuesta: basic | Privacidad: public | Autorizacion remota: True

### Enunciado

Escribe en Python una funcion unique_in_order(values) que reciba una lista de enteros y devuelva una lista sin repetidos, conservando el orden de la primera aparicion. No modifiques la entrada. Una lista vacia debe devolver []. Entrega solo la funcion, sin imports, explicaciones ni llamadas de ejemplo.

### Puntos esperados

- Conserva el orden de primera aparicion
- Elimina duplicados y admite negativos y cero
- Gestiona la lista vacia y no modifica la entrada

### Errores criticos

- Ordenar la salida en lugar de conservar el orden
- Modificar la entrada
- Funcion no ejecutable

### Formato

- Solo la funcion solicitada
- Sin imports ni llamadas de ejemplo

### Pruebas de referencia

```json
{
  "function": "unique_in_order",
  "preserve_inputs": true,
  "fixtures": [
    {
      "args": [
        [
          3,
          1,
          3,
          2,
          1
        ]
      ],
      "expected": [
        3,
        1,
        2
      ]
    },
    {
      "args": [
        []
      ],
      "expected": []
    },
    {
      "args": [
        [
          0,
          -1,
          0,
          -1,
          2
        ]
      ],
      "expected": [
        0,
        -1,
        2
      ]
    },
    {
      "args": [
        [
          5,
          5,
          5
        ]
      ],
      "expected": [
        5
      ]
    }
  ]
}
```

## C02: Media con ausencias

Familia: code | Dificultad propuesta: intermediate | Privacidad: public | Autorizacion remota: False

### Enunciado

Escribe en Python mean_valid(values). La lista contiene solo numeros o None. Devuelve la media de los numeros ignorando None. Si no queda ningun numero, devuelve None. El cero es un numero valido. No modifiques la lista. Entrega solo la funcion, sin imports, explicaciones ni llamadas de ejemplo.

### Puntos esperados

- Ignora solo None, no el cero
- Calcula la media de todos los numeros restantes
- Devuelve None si no hay numeros y conserva la entrada

### Errores criticos

- Excluir ceros
- Dividir por cero
- Modificar la entrada
- Funcion no ejecutable

### Formato

- Solo la funcion solicitada
- Sin imports ni llamadas de ejemplo

### Pruebas de referencia

```json
{
  "function": "mean_valid",
  "preserve_inputs": true,
  "fixtures": [
    {
      "args": [
        [
          0,
          2,
          null
        ]
      ],
      "expected": 1.0
    },
    {
      "args": [
        [
          null,
          null
        ]
      ],
      "expected": null
    },
    {
      "args": [
        []
      ],
      "expected": null
    },
    {
      "args": [
        [
          -2,
          2,
          6
        ]
      ],
      "expected": 2.0
    }
  ]
}
```

## C03: Filtro local estricto

Familia: code | Dificultad propuesta: intermediate | Privacidad: internal | Autorizacion remota: True

### Enunciado

Ejercicio sobre un catalogo ficticio interno. Escribe local_ids(models), que recibe una lista de diccionarios con clave id y una clave location opcional. Devuelve los id de las entradas cuyo location sea exactamente 'local', conservando el orden. Excluye las entradas sin location; no modifiques los datos. Entrega solo la funcion Python, sin imports, explicaciones ni llamadas de ejemplo.

### Puntos esperados

- Incluye solo location exactamente igual a local
- Excluye remotos y valores ausentes
- Conserva orden y datos de entrada

### Errores criticos

- Incluir ubicaciones ausentes o remotas
- Modificar la entrada
- Funcion no ejecutable

### Formato

- Solo la funcion solicitada
- Sin imports ni llamadas de ejemplo

### Pruebas de referencia

```json
{
  "function": "local_ids",
  "preserve_inputs": true,
  "fixtures": [
    {
      "args": [
        [
          {
            "id": "a",
            "location": "local"
          },
          {
            "id": "b",
            "location": "remote"
          },
          {
            "id": "c"
          }
        ]
      ],
      "expected": [
        "a"
      ]
    },
    {
      "args": [
        []
      ],
      "expected": []
    },
    {
      "args": [
        [
          {
            "id": "x",
            "location": "LOCAL"
          },
          {
            "id": "y",
            "location": null
          }
        ]
      ],
      "expected": []
    },
    {
      "args": [
        [
          {
            "id": "b",
            "location": "local"
          },
          {
            "id": "a",
            "location": "local"
          }
        ]
      ],
      "expected": [
        "b",
        "a"
      ]
    }
  ]
}
```

## C04: Seleccion y desempate

Familia: code | Dificultad propuesta: intermediate | Privacidad: public | Autorizacion remota: True

### Enunciado

Escribe best_candidate(items). Cada diccionario tiene id (texto unico), score (numero) y eligible (booleano). Devuelve el id del candidato elegible con mayor score. Si empatan, devuelve el id menor en orden alfabetico. Si no hay elegibles devuelve None. No modifiques la lista ni sus diccionarios. Entrega solo la funcion Python, sin imports, explicaciones ni llamadas de ejemplo.

### Puntos esperados

- Filtra los no elegibles antes de comparar
- Maximiza score y desempata por id alfabetico
- Devuelve None sin elegibles y conserva la entrada

### Errores criticos

- Elegir un no elegible
- Desempate incorrecto
- Modificar la entrada
- Funcion no ejecutable

### Formato

- Solo la funcion solicitada
- Sin imports ni llamadas de ejemplo

### Pruebas de referencia

```json
{
  "function": "best_candidate",
  "preserve_inputs": true,
  "fixtures": [
    {
      "args": [
        [
          {
            "id": "a",
            "score": 0.99,
            "eligible": false
          },
          {
            "id": "b",
            "score": 0.6,
            "eligible": true
          }
        ]
      ],
      "expected": "b"
    },
    {
      "args": [
        [
          {
            "id": "z",
            "score": 0.8,
            "eligible": true
          },
          {
            "id": "a",
            "score": 0.8,
            "eligible": true
          }
        ]
      ],
      "expected": "a"
    },
    {
      "args": [
        []
      ],
      "expected": null
    },
    {
      "args": [
        [
          {
            "id": "a",
            "score": 1,
            "eligible": false
          }
        ]
      ],
      "expected": null
    },
    {
      "args": [
        [
          {
            "id": "a",
            "score": -2,
            "eligible": true
          },
          {
            "id": "b",
            "score": -1,
            "eligible": true
          }
        ]
      ],
      "expected": "b"
    }
  ]
}
```

## S01: Resultados sin conclusiones extra

Familia: summary | Dificultad propuesta: basic | Privacidad: public | Autorizacion remota: True

### Enunciado

Resume en tres puntos este informe ficticio, sin anadir conclusiones: Se probaron dos modelos locales con veinte solicitudes. En dieciocho solicitudes ambos produjeron una respuesta; en dos uno de los modelos fallo. No se evaluo la correccion de las respuestas. La siguiente fase repetira los casos fallidos y revisara manualmente la calidad.

### Puntos esperados

- Dos modelos y veinte solicitudes
- Ambos respondieron en dieciocho; en dos fallo uno
- Calidad aun sin evaluar; se repetiran fallos y revisara calidad

### Errores criticos

- Equiparar respuesta producida con respuesta correcta
- Afirmar que ambos modelos fallaron en dos solicitudes

### Formato

- Tres puntos
- Sin conclusiones no presentes

## S02: Acta con decisiones pendientes

Familia: summary | Dificultad propuesta: intermediate | Privacidad: internal | Autorizacion remota: True

### Enunciado

Acta ficticia interna: El equipo acordo mantener dos modelos locales durante el piloto. Se propuso incorporar un servicio remoto, pero la propuesta quedo pendiente de presupuesto. La persona A preparara los casos y la persona B revisara la rubrica. No se fijo fecha para la evaluacion final. Resume en un parrafo de hasta 65 palabras, diferenciando acuerdos de propuestas pendientes.

### Puntos esperados

- Se acordaron dos modelos locales
- Servicio remoto propuesto, pendiente de presupuesto
- A prepara casos y B revisa rubrica; no hay fecha final

### Errores criticos

- Dar el servicio remoto por aprobado
- Inventar una fecha

### Formato

- Un parrafo
- Hasta 65 palabras
- Distingue acuerdo y propuesta

## S03: Registro sensible ficticio

Familia: summary | Dificultad propuesta: intermediate | Privacidad: sensitive | Autorizacion remota: True

### Enunciado

Registro totalmente ficticio de una prueba, sin personas reales: Caso P-017; contacto inventado prueba@example.org. El caso contiene datos marcados como sensibles. Se ejecuto localmente. El primer intento fallo por tiempo de espera; el segundo devolvio una respuesta. La respuesta aun no ha sido revisada. Resume en dos frases, omitiendo el identificador y el correo y sin afirmar que la respuesta sea correcta.

### Puntos esperados

- Datos sensibles procesados localmente
- Primer intento fallo por tiempo de espera y segundo respondio
- Respuesta pendiente de revision

### Errores criticos

- Reproducir el identificador o el correo
- Afirmar correccion ya verificada
- Afirmar ejecucion remota

### Formato

- Dos frases
- Omite identificador y correo

## S04: Discrepancia entre fuentes

Familia: summary | Dificultad propuesta: intermediate | Privacidad: public | Autorizacion remota: False

### Enunciado

Resume en dos puntos, sin resolver la discrepancia: El registro automatico del ensayo ficticio indica doce solicitudes completadas. La hoja de revision manual indica once. Ambos registros se refieren al mismo ensayo. El equipo todavia no ha conciliado los datos y no conoce la causa de la diferencia.

### Puntos esperados

- El registro automatico indica doce y el manual once
- Se refieren al mismo ensayo y existe discrepancia
- Causa desconocida y conciliacion pendiente

### Errores criticos

- Elegir una cifra como definitiva
- Inventar una causa para la diferencia

### Formato

- Dos puntos
- Mantiene la discrepancia abierta

## W01: Invitacion a revisar el piloto

Familia: writing | Dificultad propuesta: basic | Privacidad: public | Autorizacion remota: True

### Enunciado

Redacta un correo profesional en espanol de entre 60 y 90 palabras, incluido el asunto, dirigido al equipo de un proyecto ficticio. Pide revisar veinte casos del piloto antes del viernes. Indica que la rubrica esta pendiente de acuerdo y pide confirmar disponibilidad. No inventes hora, fecha de calendario, enlace ni nombre de persona.

### Puntos esperados

- Pide revisar veinte casos antes del viernes
- Rubrica pendiente de acuerdo
- Solicita confirmar disponibilidad

### Errores criticos

- Afirmar que la rubrica esta aprobada
- Inventar fecha, hora, enlace o persona

### Formato

- Entre 60 y 90 palabras incluyendo asunto
- Asunto y cuerpo de correo
- Tono profesional

## W02: Explicar una abstencion

Familia: writing | Dificultad propuesta: intermediate | Privacidad: internal | Autorizacion remota: True

### Enunciado

Escribe un mensaje de interfaz para un escenario ficticio interno. Ningun modelo local alcanza la calidad minima solicitada y la politica interna impide usar modelos remotos. Explica la abstencion y sugiere revisar el umbral con la persona responsable, sin cambiarlo automaticamente ni sugerir enviar los datos fuera. Usa entre 35 y 60 palabras y un tono claro, sin tecnicismos.

### Puntos esperados

- No hay modelo local que cumpla la calidad minima
- Politica interna impide remotos
- Propone revisar umbral con la persona responsable sin modificarlo

### Errores criticos

- Proponer enviar datos al remoto
- Afirmar que se ha rebajado el umbral
- Afirmar que se ha ejecutado la solicitud

### Formato

- Entre 35 y 60 palabras
- Tono claro sin tecnicismos

## W03: Nota sin informacion personal

Familia: writing | Dificultad propuesta: intermediate | Privacidad: sensitive | Autorizacion remota: True

### Enunciado

Todos los datos siguientes son ficticios: Caso P-204, correo contacto@example.org. Hubo un fallo de tiempo de espera durante una prueba local y la revision esta pendiente. Redacta una nota de seguimiento de entre 45 y 75 palabras para el equipo. No reproduzcas el identificador ni el correo. Explica el fallo, solicita revision y no inventes causa, responsable ni fecha de solucion.

### Puntos esperados

- Fallo por tiempo de espera durante prueba local
- Revision pendiente y solicitud de revisarla
- Sin prometer solucion ni inventar causa o responsable

### Errores criticos

- Revelar identificador o correo
- Inventar causa, responsable o fecha de solucion

### Formato

- Entre 45 y 75 palabras
- Nota dirigida al equipo
- Omite datos ficticios identificadores

## W04: Redaccion cientifica prudente

Familia: writing | Dificultad propuesta: intermediate | Privacidad: public | Autorizacion remota: False

### Enunciado

Reescribe de forma rigurosa en un parrafo de entre 45 y 75 palabras esta afirmacion: 'Nuestro sistema siempre elige el mejor modelo y reduce las emisiones un 50 %'. Los unicos hechos disponibles son que el prototipo funciona con dos modelos locales y que se ha comprobado la generacion de respuestas. Todavia no se han evaluado calidad, emisiones ni ahorro economico. No anadas datos.

### Puntos esperados

- Prototipo funcional con dos modelos locales y generacion comprobada
- No se ha demostrado seleccion optima ni reduccion de emisiones
- Calidad, emisiones y ahorro economico pendientes de evaluacion

### Errores criticos

- Mantener como demostrado el ahorro del 50 %
- Garantizar eleccion del mejor modelo
- Inventar resultados

### Formato

- Un parrafo
- Entre 45 y 75 palabras
- Tono academico prudente

