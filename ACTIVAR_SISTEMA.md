# Activar cuentas, misiones y monedas

La carpeta está compilada para GitHub Pages. Las completaciones se guardan en Firebase; los saldos y las misiones se verifican mediante GitHub Actions, sin Cloud Functions ni un servidor contratado.

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

Hasta que esta ejecución termine, la web muestra una vista previa y el saldo inicial como pendiente. No se simula un depósito ni se permite gastar ese saldo de muestra.

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

A medianoche de Uruguay asigna el nuevo período en su primera ejecución. Hasta entonces puede mostrarse la asignación anterior o una propuesta. No hace falta que entre un administrador diariamente.

Registrar niveles y porcentajes es inmediato cuando Firebase confirma. Recompensas, compras, cambios de misiones y casillas se procesan en la próxima ejecución. «Solicitar comprobación» deja una solicitud; no inicia GitHub Actions desde el navegador ni finge una consulta nueva.

Las estadísticas se miden desde una consulta inicial válida. Si faltan datos actuales, la misión queda esperando su línea de base. Una consulta posterior al vencimiento no permite fechar las ganancias del período anterior y no concede retroactivamente ese progreso. Las completaciones manuales fechadas dentro del período sí pueden reconocerse después.

Los saldos, el catálogo verificado, los perfiles verificados y las asignaciones no admiten escritura del navegador, ni siquiera desde una sesión de administrador de la página. La tarea usa acceso privilegiado del proyecto; las credenciales permanecen en el secret de GitHub.

## Si algo no se activa

- **Cuenta pendiente:** vinculá su UID desde Ajustes o el workflow y volvé a iniciar sesión.
- **Vista previa / saldo inicial pendiente:** falta ejecutar correctamente el verificador.
- **PERMISSION_DENIED:** revisá las reglas nuevas, el rol y la vinculación recíproca en `members` / `playerOwners`.
- **Consulta antigua:** revisá el último resultado de Actions. No hay que cambiar la contraseña de la página.
- **Credenciales de otro proyecto:** usá la cuenta de servicio de `gd-cucumberlist`.
- **No aparecen niveles nuevos:** esperá la próxima consulta del catálogo. Los metadatos de niveles nuevos deben coincidir con el catálogo confiable.

Documentación técnica: https://firebase.google.com/docs/database/rest/auth · https://firebase.google.com/docs/database/rest/save-data · https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets
