# Activar Cucumberlist 4

La carpeta está compilada para GitHub Pages. Firebase mantiene las cuentas privadas, las compras y los cambios de perfil en vivo. GitHub Actions consulta GD y prepara asignaciones, sin Cloud Functions ni un servidor contratado.

## Actualización desde la versión 3

1. Subí todos los archivos nuevos al mismo repositorio, incluyendo `.github`, `data`, `scripts` y `assets`. Conservá el mismo `data/economy-bootstrap.json`.
2. Publicá las reglas nuevas de `firebase.rules.json` en Firebase Console → Realtime Database → Rules.
3. Ejecutá **Verificar misiones y monedas** una vez con el workflow actualizado. Reutilizá el secret existente; no hace falta crear usuarios, regenerar claves ni volver a vincular UIDs.
4. Publicá el sitio y recargá la página.

La tarea publica el catálogo confiable de 102 cosméticos, copia las asignaciones dentro de cada cuenta y migra los cosméticos equipados a la apariencia pública. Conserva monedas, recibos, inventarios y progresos. `data/game-preview.json` queda reemplazado por un archivo vacío de cuentas para retirar la antigua muestra pública; no lo sustituyas por una copia de Firebase.

## 1. Publicar la web y las reglas

Subí el contenido de esta carpeta al repositorio, incluyendo `.github`. Conservá los archivos de `data`; especialmente `economy-bootstrap.json`, que fija la entrega inicial y no debe regenerarse.

En Settings → Pages, seleccioná GitHub Actions y ejecutá **Publicar Cucumberlist**.

Respaldá tus datos y reglas actuales. Publicá el contenido de `firebase.rules.json` en **Firebase Console → Realtime Database → Rules**. No lo pegues en Data ni reemplaces la raíz de la base. Subir ese JSON a GitHub no publica las reglas en Firebase.

La actualización mantiene los datos existentes de `editors`, pero esa ruta deja de conceder permisos globales. Los roles nuevos son `admins` y `members`. Los antiguos usuarios de Authentication se conservan.

## 2. Preparar el verificador una sola vez

1. En el proyecto Firebase `gd-cucumberlist`, abrí Configuración del proyecto → Cuentas de servicio. Generá una clave privada para una cuenta de servicio del proyecto con permisos de administración de Realtime Database. Podés usar la cuenta del Admin SDK del proyecto.
2. En GitHub → Settings → Secrets and variables → Actions → Secrets, creá **FIREBASE_SERVICE_ACCOUNT**. Su valor es el contenido completo del JSON de esa cuenta de servicio. No subas el archivo al repositorio ni lo pegues en el JavaScript.
3. En Firebase Authentication → Users, copiá el UID de la cuenta que será administradora de la página.
4. En GitHub → Secrets and variables → Actions → Variables, creá **INITIAL_ADMIN_UID** con ese UID.
5. En Actions, ejecutá **Verificar misiones y monedas → Run workflow**. Para vincular también a ese usuario con su jugador, completá los campos opcionales `link_uid` y `link_player`.

El script exige que la cuenta de servicio pertenezca a `gd-cucumberlist`. Solo crea el administrador inicial cuando la colección `admins` está vacía. Después podés quitar la variable INITIAL_ADMIN_UID; no borres tu rol de Firebase.

Esta primera ejecución acredita automáticamente:

| Jugador | Demons registrados | Puntos | Monedas iniciales |
|---|---:|---:|---:|
| thiaguinhio | 179 | 11.680 | 5.916 |
| michaeelp | 22 | 447 | 529 |
| nzrv / Nzrvv | 58 | 2.387 | 1.637 |

Fórmula: **20 × demons registrados + floor(puntos / 5)**. La operación se registra como `retro_v1`, una sola vez por jugador. Cambiar de UID no vuelve a pagarla. Los niveles incluidos también quedan marcados como ya recompensados.

Hasta que esta ejecución termine, la cuenta muestra sus asignaciones como pendientes. No se publican vistas previas con las misiones o inventarios de los tres jugadores.

## 3. Vincular las tres cuentas

Email/Password debe estar habilitado en Authentication. Agregá `TU_USUARIO.github.io` en sus dominios autorizados, sin la ruta del repositorio.

Cada jugador puede crear su cuenta desde la página o conservar la que ya tenía. Al iniciar sesión sin asociación verá su UID. El administrador debe entrar a **Ajustes → Vincular usuarios**, elegir el jugador y pegar ese UID. También puede vincularse mediante los campos del workflow.

Asociaciones de GD:

| Jugador | Cuenta de GD | Account ID |
|---|---|---|
| thiaguinhio | thiaguinhio | 18823987 |
| michaeelp | michaeelp | 24854395 |
| nzrv | Nzrvv | 13334739 |

Un UID solo puede representar a un jugador y cada jugador tiene un propietario. El panel requiere confirmar los reemplazos. Después de asociarse, el jugador debe volver a iniciar sesión.

La asociación la autoriza el administrador; no es un inicio de sesión oficial de Geometry Dash y nunca se necesita su contraseña de GD. El Account ID permanece estable aunque cambie el nombre.

## Funcionamiento posterior

**Verificar misiones y monedas** está programado cada 15 minutos, a los minutos 7, 22, 37 y 52. GitHub puede retrasar ejecuciones o desactivar programaciones de repositorios inactivos; revisá Actions si aparece una consulta antigua. Podés ejecutar el workflow manualmente cuando quieras.

La tarea consulta los tres perfiles públicos de GD y el catálogo de Google Sheets. Conserva la última consulta válida cuando una fuente falla. No escribe fechas falsas ni rellena datos desconocidos.

A medianoche de Uruguay asigna el nuevo período en su primera ejecución. Hasta entonces puede mostrarse la asignación anterior o el estado pendiente. No hace falta que entre un administrador diariamente.

Registrar niveles y porcentajes, comprar, equipar y editar el perfil o sus ajustes es inmediato al confirmar Firebase. Los premios de niveles, misiones, desafíos y bingo también pueden cobrarse en vivo cuando las reglas comprueban sus condiciones; el cobro automático se puede desactivar en Ajustes.

Las estadísticas públicas de GD se consultan cada 15 minutos. Cambiar misiones o casillas y pedir una verificación conserva el procesamiento programado. Una solicitud no inicia GitHub Actions desde el navegador ni representa una consulta nueva de GD.

Las estadísticas se miden desde una consulta inicial válida. Si faltan datos actuales, la misión queda esperando su línea de base. Una consulta posterior al vencimiento no permite fechar las ganancias del período anterior y no concede retroactivamente ese progreso. Las completaciones manuales fechadas dentro del período sí pueden reconocerse después.

El navegador no puede fijar un saldo libremente: solo puede confirmar una compra o una recompensa respaldada por un recibo nuevo y validado, junto con su saldo e inventario correspondientes. Los recibos existentes no se pueden borrar ni reescribir. El catálogo confiable, los perfiles GD verificados y las asignaciones permanecen reservados al verificador. Sus credenciales siguen en el secret de GitHub.

## Qué puede ver cada cuenta

`gameState/JUGADOR`, `runs/JUGADOR`, `preferences/JUGADOR` y `requests/JUGADOR` solo permiten lectura a su UID vinculado mediante `members` y `playerOwners`. Las raíces de asignaciones y cooperativas tampoco admiten lectura desde el navegador. El panel de administrador no permite consultar las cuentas privadas ajenas; su función es gestionar asociaciones y datos públicos.

`publicProfiles` contiene únicamente nombre visible, biografía, cosméticos equipados y preferencia de actividad. Los perfiles, la lista, el ranking y las completaciones siguen siendo públicos. El objetivo público del perfil sigue compartido; los porcentajes de las misiones se guardan por separado en `runs`.

## Si algo no se activa

- **Cuenta pendiente:** vinculá su UID desde Ajustes o el workflow y volvé a iniciar sesión.
- **Cuenta pendiente / versión anterior:** falta ejecutar correctamente el verificador actualizado.
- **PERMISSION_DENIED:** revisá las reglas nuevas, el rol y la vinculación recíproca en `members` / `playerOwners`.
- **Compra rechazada:** publicá las reglas v4 y ejecutá el verificador actualizado para cargar `shopCatalog`; comprobá también el saldo y la conexión.
- **Consulta antigua:** revisá el último resultado de Actions. No hay que cambiar la contraseña de la página.
- **Credenciales de otro proyecto:** usá la cuenta de servicio de `gd-cucumberlist`.
- **No aparecen niveles nuevos:** esperá la próxima consulta del catálogo. Los metadatos de niveles nuevos deben coincidir con el catálogo confiable.

Documentación técnica: https://firebase.google.com/docs/database/rest/auth · https://firebase.google.com/docs/database/rest/save-data · https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets
