# Desafíos y próximo hardest

## Preparar la actualización

1. Subí todo el contenido de esta carpeta al repositorio de la web.
2. En Firebase Console → Realtime Database → Rules, publicá el contenido del `firebase.rules.json` incluido. Conservá los datos de la base y los usuarios de Authentication.
3. Abrí la web y entrá con tu cuenta de editor. Al cargar el catálogo, se guardan los tres diarios y el semanal de ese período.

Si ves «Por fijar», el nivel es todavía una propuesta. Entrá como editor y esperá la carga del catálogo; también podés pulsar «Fijar desafíos». Los visitantes no necesitan iniciar sesión para ver los desafíos guardados ni el progreso.

## Guardar tu nivel en progreso

1. Entrá a **Desafíos → En juego · próximo hardest** y pulsá **Elegir nivel** en el jugador correcto. También está disponible desde su perfil.
2. Buscá por nombre, creador o ID y elegí un nivel pendiente del catálogo.
3. Escribí tu mejor porcentaje y pulsá **Guardar progreso**.
4. Para mejorar la marca o elegir otro nivel, usá **Actualizar objetivo**. La marca del mismo nivel nunca baja.
5. Al pasar el nivel, guardá **100**. Se registra la completación y el progreso juntos, sin duplicar una completación existente.

«Retirar objetivo actual» quita únicamente el nivel en progreso; conserva sus completaciones y puntos.

## Jugar un desafío

- **Jugar** elige ese nivel en el formulario del jugador. Guardá el porcentaje para convertirlo en su objetivo actual.
- **100 %** permite registrar la victoria del diario directamente desde su tarjeta.
- El semanal muestra el avance de los tres en el mismo nivel. Cada uno guarda su porcentaje en su objetivo.
- Cada jugador mantiene un único objetivo actual. Para contar como victoria diaria o semanal, la completación debe guardarse antes de que termine el período. La fecha utilizada es la de Firebase al registrar, no una fecha inventada del juego.

## Elección y horarios

El diario apunta a aproximadamente el 90 % del hardest de ese jugador. El semanal usa la media de los tiers de los tres hardests. Los candidatos se eligen del catálogo y deben estar pendientes para el jugador, o para los tres en el caso del semanal.

El diario renueva a medianoche de Uruguay; el semanal, cada lunes a medianoche. No se requiere un servidor nuevo: el primer editor conectado guarda las propuestas del período. Una vez fijadas, conseguir un nuevo hardest no modifica esos desafíos. Si ningún editor abre la web, se muestran las propuestas sin fijar.

Los desafíos se guardan en `desafios/diarios/AAAA-MM-DD/jugador` y `desafios/semanales/fecha-del-lunes`. Los objetivos se guardan en `objetivos/jugador`. Las completaciones continúan usando `pasados` e `historial`.
