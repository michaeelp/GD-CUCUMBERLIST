# GD Cucumberlist — GitHub Pages

Subí todo el contenido de esta carpeta al repositorio, incluyendo `.github`, y seleccioná **Settings → Pages → Source → GitHub Actions**. `index.html` está en la raíz y la aplicación ya está compilada; no necesitás Node para publicarla. Las rutas son relativas y admiten cualquier nombre de repositorio.

Para activar la actualización, seguí **ACTIVAR_SISTEMA.md**: publicar las reglas nuevas, configurar el verificador y asociar cada UID con su jugador. Las cuentas y completaciones anteriores se conservan. No hace falta Cloud Functions ni un backend contratado.

## Funciones

- Demons diarios al 50 % del tier del hardest personal.
- Semanal al 60 % de la media de los tres hardests.
- Cuatro misiones personales diarias, con niveles, porcentajes y estadísticas del perfil.
- Easy Demon cooperativo diario para los tres.
- Bingo mensual 4 × 4, adaptado al tiempo disponible, con dos cambios de casilla.
- Ruleta con dificultad, tier absoluto o relativo, pendientes personales o del grupo, creador, exclusiones, resultados recientes y uno o tres resultados.
- Objetivo actual y mejor porcentaje, separado del progreso de quests.
- Monedas, XP, tienda de títulos/colores/insignias, compras y movimientos.
- Entrega inicial por puntuación y demons registrados, una sola vez: thiaguinhio 5.916; michaeelp 529; nzrv 1.637.
- Cada jugador modifica exclusivamente sus registros. El administrador gestiona asociaciones y correcciones.

Horarios: America/Montevideo. El diario renueva a medianoche; el semanal, el lunes; el bingo, al cambiar de mes. Las asignaciones y verificaciones se procesan en la primera ejecución programada de ese período.

## Datos y verificación

Firebase mantiene completaciones y porcentajes en tiempo real. El verificador de GitHub Actions consulta GD y Sheets cada 15 minutos y procesa recompensas y compras. Los perfiles, estadísticas, saldos y asignaciones verificados son de solo lectura para el navegador. Las partidas concretas y porcentajes son declaraciones manuales del jugador.

Las consultas se muestran con fecha. Una consulta posterior al vencimiento no demuestra en qué momento se ganaron estrellas, lunas o diamantes. Las misiones de estadísticas que no pudieron verificarse a tiempo no reciben ganancias atribuidas al día anterior.

La actualización pública de iconos y detalles de niveles continúa mediante **Publicar Cucumberlist**, al hacer push, manualmente y cada seis horas. El verificador no necesita volver a publicar el sitio para actualizar Firebase.

## Archivos

- `index.html`, `assets/`, `data/`: web lista para publicar.
- `data/economy-bootstrap.json`: base fija de la entrega inicial; no regenerar en actualizaciones.
- `firebase.rules.json`: permisos de esta versión.
- `.github/workflows/pages.yml`: publicación de Pages e iconos.
- `.github/workflows/verificar.yml`: misiones, perfiles, compras y monedas.
- `scripts/game_engine.py`: reglas de selección, progreso y economía.
- `scripts/verificar-juego.py`: verificador autenticado.
- `cuentas.json`: cuentas de GD.
- `fuente/`: código React/TypeScript editable y compilación opcional.
- `tests/`: pruebas del motor y del verificador.
- `PRUEBAS.md`: verificaciones y límites.

Para probar el paquete localmente, servilo por HTTP; por ejemplo, `python3 -m http.server 8000`. Abrí `http://localhost:8000`. No uses `file://`.
