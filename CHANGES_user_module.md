# CHANGES: User module updates

Fecha: 2025-11-05

Resumen breve
- Se añadió un dashboard como vista principal y se ocultó el enlace visible de "Iniciar Sesión" en la navegación.
- Al cerrar sesión (logout) la aplicación redirige a la vista de login (`#/login`) y el dashboard queda oculto hasta que se vuelva a iniciar sesión.

Archivos modificados / añadidos
- `app.py` — nueva ruta `/dashboard` que sirve la plantilla `dashboard.html`.
- `templates/dashboard.html` — nueva plantilla con welcome y tarjetas informativas.
- `templates/inicio.html` — se ocultó/eliminó el elemento de menú "Iniciar Sesión" (para no mostrarlo por defecto).
- `static/js/app_user.js` — cambios en enrutado Angular:
  - La ruta por defecto `/` ahora carga `/dashboard`.
  - Se añadió la ruta `/login` para la plantilla de login.
  - Se añadió `dashboardCtrl` para cargar la información del usuario y redirigir al login si no hay sesión.
  - Se modificó `$rootScope.logout()` para limpiar el estado y redirigir a `#/login` (además de recargar la página para forzar la actualización de vistas protegidas).

Comportamiento esperado
- Al abrir la aplicación el shell `inicio.html` se sirve siempre. Angular carga por defecto la vista `/dashboard` en el `ng-view`.
- Si no existe sesión activa (o `/api/user/current` devuelve 401/false), `dashboardCtrl` redirige a `#/login` para ocultar el dashboard.
- Al pulsar el botón de logout se ejecuta `/api/logout`, el `rootScope` se limpia y el navegador se posiciona en `#/login`.

Cómo verificar rápidamente (local)
1. Instalar dependencias y arrancar la app:

   ```cmd
   D:\ProyectoFinal> pip install -r requirements.txt
   D:\ProyectoFinal> python app.py
   ```

2. Abrir en el navegador: http://127.0.0.1:5000/
   - Si no hay sesión activa: deberías ser redirigido a `#/login` desde el dashboard.
   - Iniciar sesión con credenciales válidas (si la base de datos está disponible y el usuario existe).
   - Después de iniciar sesión, volverás al dashboard y verás el nombre de usuario.
   - Pulsa "Salir" y confirma que quedas en `#/login` y que el dashboard ya no está accesible hasta iniciar sesión.

Notas y puntos importantes
- El cambio de comportamiento (ocultar el login del menú) es intencional para priorizar el dashboard como vista por defecto; si prefieres que el enlace siga visible, basta con restaurar el `<li>` correspondiente en `templates/inicio.html`.
- Si la aplicación responde con 401 en `/api/user/current` es porque no hay sesión o la base de datos no está accesible en este entorno. En ese caso crea la BD y la tabla `users` o ajusta `config/database.py`.

Rollback rápido
- Para revertir este cambio y volver al comportamiento anterior (login visible y `/#/` apuntando a login):
  1. Restaurar `static/js/app_user.js` desde `archive/static_js_app_legacy.js` o desde control de versión.
  2. Restaurar el `<li>` de "Iniciar Sesión" en `templates/inicio.html`.
  3. Eliminar `templates/dashboard.html` y la ruta `/dashboard` en `app.py` (opcional).

Autor: Cambios aplicados automáticamente por el asistente de desarrollo (modificado el 2025-11-05).
Resumen de cambios: Módulo reducido a 'usuario' solamente

Se eliminaron o neutralizaron los módulos de "postres" y "ingredientes". El proyecto ahora conserva únicamente la funcionalidad del módulo de usuario (autenticación y gestión básica de sesión).

Archivos eliminados o reemplazados:

- routes/postre_routes.py  (eliminado)
- routes/ingrediente_routes.py  (eliminado)
- models/postre.py  (eliminado)
- models/ingrediente.py  (eliminado)
- repositories/postre_repository.py  (eliminado)
- repositories/ingrediente_repository.py  (eliminado)
- services/postre_service.py  (eliminado)
- services/ingrediente_service.py  (eliminado)
- templates/postres.html  (eliminado)
- templates/ingredientes.html  (eliminado)
- templates/tbodyPostres.html  (eliminado)
- templates/tbodyIngredientes.html  (eliminado)

Archivos modificados:

- app.py
  - Se quitaron las importaciones y el registro de blueprints de `postre` y `ingrediente`.

- templates/inicio.html
  - Se removieron los enlaces del menú a Postres e Ingredientes.
  - Se actualizó la carga del JS principal a `static/js/app_user.js`.

- static/js/app_user.js (nuevo)
  - Nuevo archivo JavaScript mínimo que implementa autenticación y verificación de sesión para el módulo de usuario.

- services/pusher_service.py
  - Reemplazado por un stub (Pusher ya no se usa en la versión reducida).

Notas importantes:

- El archivo `static/js/app.js` grande que contenía la lógica de Postres/Ingredientes permanece en el repositorio pero ya no se carga desde `inicio.html`. Si deseas eliminarlo completamente, puedes borrarlo manualmente.

- Para revertir cambios manualmente, recupera los archivos listados arriba desde tu control de versiones (git) o copia de seguridad.

Pruebas rápidas recomendadas:

1. Instala dependencias (si es necesario):
   - `pip install -r requirements.txt`
2. Ejecuta la app en modo desarrollo (Windows/cmd):
   - `python app.py`
3. Accede a `http://127.0.0.1:5000/` y prueba el login/registro de usuarios.

Si quieres que también elimine `static/js/app.js` por completo o actualice más plantillas, dímelo y lo hago.
