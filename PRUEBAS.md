# Verificación de esta versión

- TypeScript y compilación estática para GitHub Pages.
- 14 pruebas de integridad de completaciones, puntuación, historial y sincronización.
- 13 pruebas de períodos y selección de desafíos, ahora al 50 % y al 60 % de la media.
- 6 pruebas de rutas, perfiles de GD y compatibilidad con Pages.
- 16 pruebas del motor: saldo retroactivo único, retirada y reingreso de niveles, precio de recompensas tomado del catálogo confiable, líneas de base, exclusión de consultas fuera de plazo, progreso manual separado del objetivo, bonus cooperativo, compras duplicadas, saldo insuficiente, bingo tardío, límites de reemplazos y conservación de datos.
- Renderizado React del inicio, perfiles, desafíos, misiones, bingo, tienda, monedas y ruleta.
- Reglas ejecutadas en el emulador real de Firebase: asociación recíproca de cuentas; lectura privada de UIDs; permisos propios; rechazo de edición ajena, tiers falsos, ascenso a administrador, saldo directo, perfiles falsos y solicitudes reescritas; metadatos nuevos limitados al catálogo confiable; escritura atómica del 100 %.
- Verificador real ejecutado con el emulador: saldos 5.916 / 529 / 1.637, ejecución repetida sin duplicados, vinculación UID, preservación de las 259 completaciones y de nodos ajenos, una sola compra ante dos solicitudes y transacciones concurrentes con ETag.
- Integridad del ZIP, recursos enlazados y rutas relativas.

No se configuró tu GitHub, no se crearon usuarios y no se publicaron reglas ni monedas en el Firebase de producción. La tarea se entrega lista para activar siguiendo ACTIVAR_SISTEMA.md.

No se realizó una prueba visual ni de interacción en navegador real porque el controlador de navegador de Sites no estaba disponible. Se verificaron compilación, renderizado, datos, reglas y lógica contra el emulador. La autenticación OAuth del verificador requiere el secret de tu proyecto y no se ejecutó contra producción.
