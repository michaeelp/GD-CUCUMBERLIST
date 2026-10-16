# Desafíos, misiones y bingo

## Demons diarios y semanal

El diario apunta al 50 % del tier del hardest del jugador; el semanal, al 60 % de la media de los tres hardests. Se eligen candidatos pendientes cercanos a esas referencias y se evitan repeticiones recientes si hay alternativas.

El verificador fija las asignaciones. Un nuevo hardest o una recarga no las modifica durante el período. En la migración a esta versión se conserva una copia de las asignaciones antiguas y se aplican las nuevas referencias.

## Misiones

Cada jugador tiene cuatro misiones: nivel, porcentaje/completación y dos de estadísticas. Puede cambiar una misión no completada por día. Hay una recompensa por misión y 75 monedas adicionales por completar las cuatro.

Los niveles y porcentajes se registran manualmente desde la cuenta del jugador. Los porcentajes de quests no reemplazan el próximo hardest. El progreso automático usa consultas verificadas del perfil y una línea de base, sin retroceder en las ganancias ya observadas.

La cooperativa asigna un Easy pendiente para los tres. Cada uno cobra 60 monedas por su completación; cuando terminan los tres, recibe otras 90. La misión y el bonus son independientes del diario y semanal.

## Bingo

Tablero personal de 16 objetivos. Las metas se reducen si empieza avanzado el mes. No requiere rachas perfectas. Si el semanal supera un rango razonable para el jugador, esa casilla se sustituye por una misión accesible.

Premios: 50 por casilla, 100 por línea y 400 por tablero completo. Incluye cuatro filas, cuatro columnas y dos diagonales. Se pueden cambiar dos casillas no completadas por mes. Los meses anteriores quedan consultables.

## Monedas

Entrega inicial fija: `20 × demons registrados + floor(puntos / 5)`.

Completación nueva: `20 + floor(tier × 2)` monedas, una sola vez por nivel y jugador. El verificador usa el tier del catálogo confiable. Retirar y volver a registrar el mismo nivel no vuelve a pagar. Los puntos del ranking mantienen `tier × 10` y son independientes de estas monedas.

Diario: 50; semanal: 100. Misiones individuales: 25 a 65 según el objetivo. Tienda: 30 títulos, 24 colores, 24 insignias, 12 temas y 12 fuentes. Las compras y el equipamiento se confirman en vivo; los cambios de misión o casilla siguen procesándose con el verificador.

Las compras y los cobros del navegador se guardan mediante operaciones atómicas validadas por las reglas de Firebase. El verificador conserva las transacciones condicionales con ETag para no sobrescribir operaciones simultáneas. Cada premio tiene una clave estable. Duplicar una solicitud o volver a iniciar sesión no duplica monedas.

Las partidas manuales no se verifican contra una API de récords individuales de GD. La integridad de la economía protege el saldo y la unicidad de los cobros, no demuestra cómo se jugó un nivel.

## Horarios

America/Montevideo: diario a las 00:00, semanal el lunes y bingo el primer día del mes. La tarea procesa cada cambio en su siguiente ejecución programada, normalmente dentro de 15 minutos. Puede haber demoras de GitHub.

## Privacidad

Cada cuenta solo consulta sus misiones, desafíos, bingo, saldo e inventario. La misión cooperativa se muestra dentro de la cuenta propia y utiliza las completaciones públicas del grupo para comprobar el bonus. Los perfiles y el próximo objetivo público siguen compartidos.
