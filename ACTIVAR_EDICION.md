# Cuentas personales

Seguí **ACTIVAR_SISTEMA.md**. Esta versión usa `admins`, `members` y `playerOwners`; el antiguo nodo `editors` se conserva, pero deja de conceder permisos globales.

Cada usuario de Authentication mantiene su correo, contraseña y UID. El administrador asocia ese UID con un jugador. El dueño solo puede modificar sus completaciones, objetivos, porcentajes y preferencias; los demás datos son públicos de lectura.

La creación de usuarios en Authentication no concede permisos automáticamente. La asociación debe autorizarla un administrador. Nunca se utiliza la contraseña de Geometry Dash.
