# Verificacion del prototipo 0.1

Fecha: 29 de septiembre de 2026.

## Automatizada

20 pruebas unittest satisfactorias:

- Privacidad dura para todos los perfiles y datos internos/sensibles.
- Consentimiento para incluir el candidato remoto.
- Seleccion remota solo cuando es admisible, sin ejecucion remota.
- Perfil de coste, filtros de presupuesto y de calidad, abstencion.
- Deteccion heuristica de correo electronico y bloqueo remoto.
- Limites de normalizacion independientes del filtro de privacidad.
- Suma de pesos, aportaciones WSM y rango de puntuaciones.
- Validacion de entradas vacias, valores negativos, NaN y rangos.
- Ausencia del contenido en decisiones e historial.
- Proteccion de sesion y Host.
- Persistencia y borrado sobre una base de datos temporal de prueba.
- Bloqueo del proveedor no configurado sin hacer llamadas.
- Respuesta Ollama simulada y rechazo de alias cloud.
- Registro de ejecuciones bloqueadas y fallidas sin contenido de las solicitudes.
- Reversion de transacciones fallidas y cierre de conexiones SQLite.

Compilacion Vite correcta; instalacion npm sin vulnerabilidades reportadas.

## Navegador

- Seleccion inicial: dos locales admisibles, remoto excluido.
- Cambio de perfil: invalida el resultado anterior y modifica la seleccion.
- Caso de presupuesto cero: abstencion, sin ejecucion.
- Caso ficticio sensible: filtro local y remoto deshabilitado.
- Catalogo y deteccion de Ollama inactivo.
- Historial de las decisiones de prueba.
- Revision visual en escritorio 1440 x 1000 y movil 390 x 844.
- Ancho del documento movil igual al viewport: 390 px.
- Grafico de pesos visible; sin errores de consola observados.

## Limites

No se ha ejecutado inferencia real: Ollama no estaba activo y no se han
vinculado ni descargado modelos. No se han medido energia, emisiones o calidad.
Las pruebas del adaptador usan un proveedor simulado. La exportacion JSON
esta implementada; no se verifico una descarga completa mediante navegador.
No se ha realizado una auditoria de seguridad ni una prueba de carga.
Las decisiones creadas durante la comprobacion visual son datos de demostracion.
