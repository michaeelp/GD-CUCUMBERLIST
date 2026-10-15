# GD Cucumberlist — GitHub Pages

Esta carpeta es el repositorio listo para subir. `index.html` está en la raíz y los archivos ya están compilados. No necesitás Node, Vite, un proxy ni Cloud Functions para publicarla.

## Publicar

1. Creá un repositorio público en GitHub y subí **todo el contenido de esta carpeta**, incluyendo `.github`. Dejá `index.html`, `assets`, `data` y `.github` directamente en la raíz del repositorio.
2. Entrá a **Settings → Pages → Build and deployment → Source** y elegí **GitHub Actions**.
3. En **Actions**, abrí **Publicar Cucumberlist → Run workflow**. Al terminar, GitHub muestra el enlace de tu página.

El flujo también publica con cada push a `main` o `master` y está programado cada 6 horas. Puede demorarse según GitHub. Si el repositorio permanece inactivo y GitHub desactiva la programación, podés reactivar el flujo en Actions. Un fallo de GD o Sheets conserva los datos guardados y no impide publicar la copia disponible.

Las rutas son relativas. Sirve tanto en `usuario.github.io/repositorio/` como en `usuario.github.io/` o un dominio propio. No hay que editar el nombre del repositorio dentro del código.

Si preferís la publicación desde una rama, también podés seleccionar **Deploy from a branch → main → /(root)** para servir la copia incluida. Para que las actualizaciones automáticas de datos se publiquen, usá la opción **GitHub Actions** indicada arriba.

## Cuentas ya vinculadas

| Jugador de Cucumberlist | Cuenta pública GD | Account ID |
|---|---|---|
| thiaguinhio | thiaguinhio | 18823987 |
| michaeelp | michaeelp | 24854395 |
| nzrv | Nzrvv | 13334739 |

El nombre de jugador `nzrv` y sus registros de Firebase se conservan. Su perfil, estadísticas y sus nueve formas equipadas corresponden a **Nzrvv**. Los IDs se verificaron contra los servidores públicos de GD.

## Cómo se actualizan los datos

- **Completaciones, puntajes e historial:** Firebase Realtime Database en tiempo real, con la configuración original.
- **Catálogo de demons:** Google Sheets directamente desde el navegador; además queda una copia publicada como respaldo.
- **Perfiles, iconos y datos extra de niveles:** el flujo de GitHub Actions consulta información pública de GD al publicar y cada 6 horas. No son datos de GD en tiempo real. El botón «Recargar datos» lee la última consulta publicada; no fuerza una sincronización del juego.
- **Estrellas, descargas y otros detalles:** se guardan para los niveles consultados. Si un nivel no tiene datos publicados, la ventana conserva la información de Cucumberlist y explica la ausencia de datos extra.

El actualizador solo realiza lecturas de Firebase y de los servidores de GD. No modifica la base, no necesita contraseñas ni claves privadas y no ejecuta migraciones. Los sprites, fuente y SDK iniciales están dentro de esta carpeta.

En repositorios públicos, GitHub permite utilizar runners estándar de Actions sin consumir minutos de pago. No hace falta contratar un Worker ni un backend independiente. Consultá las condiciones y límites vigentes de GitHub.

## Agregar y quitar completaciones

La web ya apunta a tu Firebase original. **La publicación en Pages no configura los permisos de Firebase.** Para habilitar la edición segura, seguí `ACTIVAR_EDICION.md`: habilitar Email/Password, crear un usuario, autorizar su UID y revisar/publicar `firebase.rules.json`.

Si ya hiciste esos pasos, no hay que repetirlos. Añadí `TU_USUARIO.github.io` a los dominios autorizados de Authentication, sin la ruta del repositorio, si Firebase lo requiere. No guardes la contraseña en GitHub.

## Mantener las cuentas

`cuentas.json` contiene la asociación entre los nombres de la lista y las cuentas de GD. Para corregir una cuenta, editá su Account ID o nombre y ejecutá **Publicar Cucumberlist**. Si mantenés un Account ID correcto, un cambio de nombre de GD no pierde la asociación. Después podés seleccionar la cuenta publicada desde los ajustes de editor.

## Archivos principales

- `index.html`, `assets/`: aplicación compilada y recursos.
- `data/`: últimas consultas públicas verificadas.
- `cuentas.json`: asociación de cuentas de GD.
- `.github/workflows/pages.yml`: publicación y actualización automática.
- `scripts/actualizar-datos.py`: actualizador de lectura y retratos; usa Python y Pillow.
- `firebase.rules.json`: reglas revisables de edición.
- `PRUEBAS.md`: comprobaciones realizadas y límites.
- `CREDITOS.md`: recursos y licencias.

Podés probar localmente con `python3 -m http.server 8000` y abrir `http://localhost:8000`. No abras `index.html` con `file://`.

Documentación oficial del flujo de Pages: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
