# Código editable

La web de la carpeta superior ya está compilada. No necesitás instalar nada para publicarla.

Para editar y recompilar: instalá Node 22.13 o posterior, ejecutá `npm install` en esta carpeta y después `npm run build`. El comando actualiza el index y los bundles de la carpeta superior conservando sus datos, iconos y reglas.

Comprobaciones: `npm run typecheck`, `npm test`, `npm run test:competition`, `npm run test:pages`, `npm run test:render`, `npm run test:rewards`. Las pruebas del verificador están en `../tests` y las reglas pueden ejecutarse con el emulador de Realtime Database.

No regeneres `../data/economy-bootstrap.json` al recompilar: es la base fija de la entrega inicial. No se incluyen secretos ni contraseñas.

El catálogo está en `../data/shop.json` y las versiones en `../data/releases.json`. El verificador publica el catálogo confiable en Firebase; cambiar solo el JSON estático no cambia sus precios confiables.

Después de editar el generador de permisos, ejecutá `python3 ../scripts/build-rules.py` y probá `../tests/realtime_rules_test.py` con el emulador antes de publicar reglas.
