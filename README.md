# GD Cucumberlist 4 — GitHub Pages

Subí **el contenido** de esta carpeta al repositorio, incluyendo `.github`, y seleccioná **Settings → Pages → Source → GitHub Actions**. `index.html` está en la raíz; la aplicación ya está compilada. No necesitás Node para publicarla y las rutas funcionan con cualquier nombre de repositorio.

**Para actualizar desde la versión anterior:** publicá `firebase.rules.json` en Firebase y ejecutá una vez **Verificar misiones y monedas** con los scripts nuevos. Las instrucciones están en **ACTIVAR_SISTEMA.md**. Se conservan las cuentas, las completaciones, las compras y las monedas existentes.

## Privacidad y personalización

- Misiones, desafíos, bingo, saldo, movimientos, inventario y preferencias: únicamente la cuenta vinculada a ese jugador. También lo restringen las reglas de Firebase.
- Perfiles, completaciones, lista, clasificación, jugadores y estadísticas públicas: compartidos.
- La apariencia pública incluye solo los cosméticos equipados, nombre visible y biografía. No expone el inventario ni el saldo.
- Compras atómicas en tiempo real: precio confiable, saldo, recibo e inventario confirmados juntos; protección contra compras duplicadas y cambios simultáneos.
- 102 cosméticos: **30 títulos, 24 colores, 24 insignias, 12 temas y 12 fuentes**. Incluye vista previa, búsqueda, filtros e inventario propio.
- Temas y fuentes aplicados a todos los textos del perfil público.
- Ajustes de sonido, movimiento, densidad, contraste, cobro automático, confirmación de compras, página inicial, nombre, biografía y actividad del perfil.
- Historial de versiones con búsqueda, filtros, desplegables y enlaces por versión.

## Juego

Diario al 50 % del tier de tu hardest; semanal al 60 % de la media de los tres. Cuatro misiones diarias personales, Easy Demon cooperativo, bingo 4 × 4 adaptado al tiempo disponible, objetivo actual, porcentaje y ruleta con filtros.

Las recompensas que Firebase puede comprobar se cobran en vivo mediante recibos únicos. Las estadísticas nuevas de GD y las asignaciones se consultan mediante GitHub Actions cada 15 minutos; los cambios de misión o casilla se procesan en esa tarea. El servidor no comprueba récords individuales de GD: los niveles y porcentajes se registran manualmente por su jugador.

La entrega inicial sigue siendo una sola por jugador: thiaguinhio **5.916**, michaeelp **529**, nzrv **1.637** monedas. No regeneres `data/economy-bootstrap.json`.

Horarios de Uruguay: diario a medianoche, semanal el lunes y bingo al cambiar de mes. Las asignaciones se fijan en la primera ejecución de cada período.

## Archivos

- `index.html`, `assets/`, `data/`: web lista para publicar.
- `firebase.rules.json`: permisos y validación de operaciones de esta versión.
- `ACTIVAR_SISTEMA.md`: actualización, activación y asociación de cuentas.
- `.github/workflows/pages.yml`: publicación e iconos.
- `.github/workflows/verificar.yml`: consultas GD, asignaciones y verificación.
- `data/shop.json`: catálogo de cosméticos; `data/releases.json`: historial de versiones.
- `scripts/`: verificador, motor, generador de reglas y comprobación del paquete.
- `fuente/`: React/TypeScript editable y compilación opcional.
- `tests/`, `fuente/tests/`, `PRUEBAS.md`: pruebas y alcance de las comprobaciones.

Para abrirla localmente, serví la carpeta por HTTP, por ejemplo con `python3 -m http.server 8000`, y abrí `http://localhost:8000`.
