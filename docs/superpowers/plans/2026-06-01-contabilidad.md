# Plan de Implementación: Módulo Contabilidad (Ingresos y Egresos)

## Paso 1: TDD para la Base de Datos
- Crear archivo `tests/test_contabilidad.py` usando `unittest`.
- Escribir test que falla (RED): creación de transacción y obtención de balance.
- Correr test y verificar que falla.

## Paso 2: Implementar Modelos y DB Manager (GREEN)
- Añadir dataclass `Transaccion` en `database/models.py`.
- Añadir tabla `transacciones` en `init_db` en `database/db_manager.py`.
- Implementar `crear_transaccion`, `get_transacciones`, `get_balance_contable`.
- Correr test y verificar que pasa.

## Paso 3: TDD para integración automática con Órdenes
- Escribir test que falla: al llamar `crear_orden`, automáticamente debe existir un Ingreso.
- Correr test y verificar fallo.
- Modificar `crear_orden` en `db_manager.py` para registrar en `transacciones`.
- Correr test y verificar pase (GREEN).

## Paso 4: UI y Permisos
- Añadir "contabilidad" en `utils/session.py`.
- Añadir botón en `views/components/sidebar.py`.
- Crear vista `views/contabilidad_view.py`.
- Registrar vista en `views/main_window.py`.

## Paso 5: Verificación End-to-End
- Correr la app `python main.py` y verificar manualmente el flujo completo.
