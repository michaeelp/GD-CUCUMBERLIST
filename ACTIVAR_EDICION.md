# Activar la edición una sola vez

No se modificaron usuarios ni reglas de tu Firebase durante el desarrollo. La lectura ya usa la base original `gd-cucumberlist`.

1. En Firebase Console → Authentication → Sign-in method, habilitá **Email/Password**.
2. En Authentication → Users, creá una cuenta para editar. Usá una contraseña propia que no se publique en GitHub.
3. Copiá su UID.
4. En Realtime Database → Data, agregá `editors/TU_UID` con valor booleano `true`. No reemplaces la raíz de la base.
5. Respaldá los datos y las reglas actuales.
6. Revisá el archivo `firebase.rules.json` incluido y publicalo en Realtime Database → Rules. Si tenés otras rutas utilizadas por otra aplicación, conservá e integrá sus reglas antes de publicar.
7. En Authentication → Settings → Authorized domains, agregá `TU_USUARIO.github.io`, sin `/repositorio/`. Si usás dominio propio, agregá su hostname.
8. Abrí tu web de Pages, pulsá **Acceder** e ingresá con la cuenta creada.

Las reglas mantienen la lectura pública de la lista y el historial. Solo los UID de `editors` pueden editar. La aplicación no puede darse permisos a sí misma. Si las reglas anteriores admiten escritura pública, es necesario publicar las nuevas para cerrar ese acceso; ocultar botones no protege la base.

El HTML original no podrá continuar editando anónimamente después de activar las reglas nuevas. Los registros existentes se conservan. No se requieren Firestore, Cloud Functions ni contraseñas administrativas en el código.

## Si ya tenés una cuenta de editor

Para esta actualización, publicá el `firebase.rules.json` incluido en **Realtime Database → Rules**. No repitas el alta ni reemplaces los datos de la base. Las nuevas rutas `objetivos` y `desafios` tienen lectura pública y escritura limitada a los mismos UID de `editors`. La web crea sus nodos al guardar; no hace falta crearlos manualmente.

Los objetivos validan porcentajes enteros de 0 a 100 y conservan el mejor porcentaje de un mismo nivel. Los desafíos fijados son inmutables durante su período, también para editores. La web se encarga del cambio de día y semana.
