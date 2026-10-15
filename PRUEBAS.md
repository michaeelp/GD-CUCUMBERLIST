# Verificación de la edición GitHub Pages

Se conservó el comportamiento y los datos de Cucumberlist del proyecto anterior. En esa implementación pasaron 14 pruebas de integridad y las comprobaciones del emulador real de Firebase, incluidas altas simultáneas, permisos, duplicados y retiros sin pérdida de datos de otros jugadores.

Para esta edición se comprobó:

- Búsqueda exacta y consulta real de **Nzrvv**, Account ID **13334739**.
- Inclusión de sus datos públicos, retrato y recursos de las nueve formas equipadas.
- Compilación estática con base relativa y TypeScript.
- 14 pruebas de integridad y 6 pruebas específicas de Pages aprobadas; renderizado React del inicio aprobado.
- Resolución de los recursos en la raíz de un dominio y bajo una ruta de repositorio.
- El actualizador de GitHub Actions mediante ejecución real, sin escrituras en Firebase.
- Perfiles y detalles de niveles publicados como JSON local, sin llamadas a un backend inexistente.
- Conservación de los datos guardados ante fallos de servicios externos.
- Integridad del ZIP y de los recursos enlazados.

El flujo de Actions se entrega listo, pero solo puede ejecutarse y publicar en tu cuenta después de subir el repositorio y elegir GitHub Actions como origen de Pages. No se accedió a tu GitHub ni se configuró Firebase por vos.

No se realizó una prueba visual en un navegador real porque el controlador de navegador de Sites no estaba disponible. Se realizaron comprobaciones de compilación, renderizado, datos y rutas.

## Actualización: desafíos y objetivos

- 13 pruebas nuevas aprobadas: medianoche de Uruguay, lunes y cambio de año; selección reproducible; objetivos diarios basados en los hardests reales; semanal basado en la media; exclusión de niveles completados; repetición reciente; porcentaje monotónico; reinicio al cambiar de nivel; completación dentro del período; conservación de los datos originales.
- 14 pruebas de integridad y 6 de GitHub Pages continúan aprobadas. TypeScript y la compilación estática pasan.
- Renderizado React verificado para el inicio, los tres diarios, el semanal, el porcentaje del objetivo en el perfil y el aviso de reglas faltantes.
- Reglas ejecutadas contra el emulador real de Firebase: lectura pública de objetivos/desafíos; rechazo de escritura anónima y de cuentas sin autorización; validación de porcentaje; rechazo de retrocesos en la misma marca; cambio de objetivo; retiro limitado; escritura atómica del 100 % y rollback de datos inválidos; desafíos fijados inmutables; rechazo de futuros desafíos; diario independiente por jugador.
- No se escribieron desafíos, objetivos, usuarios ni reglas en el Firebase de producción. La activación requiere publicar las reglas incluidas en su consola.

No se hizo una prueba visual o de interacción en un navegador real; se mantienen las limitaciones del entorno indicadas arriba.
