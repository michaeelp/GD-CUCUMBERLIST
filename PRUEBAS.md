# Verificación de la versión 4

- TypeScript estricto y compilación estática con rutas relativas para GitHub Pages.
- 14 pruebas de integridad de completaciones, puntuación, historial y sincronización.
- 13 pruebas de períodos y desafíos al 50 % / 60 % de la media.
- 6 pruebas de rutas, perfiles GD y compatibilidad con Pages.
- 8 pruebas del progreso y los recibos del cliente: fechas, duplicados, porcentajes, estadísticas verificadas, creadores distintos, bonus y cooperativa.
- 16 pruebas del motor Python: entrega inicial única, nivel retirado/reingresado, catálogo confiable, líneas de base, vencimientos, progreso separado del objetivo, cooperativa, compras y bingo.
- Renderizado React del inicio público, desafíos de la cuenta propia, bloqueo de invitados, tienda, ajustes, log y apariencia pública sin saldo.
- Reglas anteriores de completaciones y asociación ejecutadas en el emulador real de Firebase: 259 registros preservados, porcentajes y 100 % atómicos, permisos propios y rechazo de modificaciones ajenas.
- Pruebas adicionales en el emulador real: cuentas, porcentajes, preferencias y solicitudes privados; administrador no vinculado sin acceso privado; compras instantáneas; precio manipulado; recibos e inventario protegidos; equipo comprado/gratuito; campos del perfil; cobro por nivel; dos compras simultáneas con reintento y ambos descuentos conservados.
- Todos los tipos de cobro inmediato comprobados contra las reglas: misión de nivel, porcentaje, estadísticas y Easy; elección, dos niveles, creadores distintos, combinación y contadores de actividad en bingo; bonus diario, diario/semanal, cooperativa, equipo, 16 casillas, 10 líneas y tablero completo. Se rechazaron pruebas repetidas, requisitos incompletos y cobros duplicados.
- Verificador real contra el emulador: créditos iniciales 5.916 / 529 / 1.637 sin duplicación, asociaciones, conservación de completaciones y nodos ajenos, migración de apariencia v3, catálogo de 102 productos y una compra instantánea intercalada durante el guardado del verificador: el conflicto ETag se reintentó sin perder el descuento ni el artículo.
- Integridad de 102 productos, fuentes locales y licencias, recursos HTML/CSS, ZIP y rutas bajo subcarpetas.

No se modificó tu GitHub ni el Firebase de producción. Publicá las reglas y ejecutá el verificador actualizado siguiendo ACTIVAR_SISTEMA.md.

No se realizó una prueba visual ni de interacción en navegador real porque el controlador de navegador de Sites no estaba disponible. Se verificaron compilación, renderizado, datos, reglas y lógica contra el emulador. La autenticación OAuth del verificador requiere el secret de tu proyecto y no se ejecutó contra producción.
