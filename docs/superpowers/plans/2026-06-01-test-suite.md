# Plan de Implementación: Test Suite Completa

## Paso 1: Test Runner
- Crear `run_tests.py` en la raíz.
- Correrlo para asegurar que encuentra `test_contabilidad.py` existente.

## Paso 2: Usuarios y Autenticación (`test_usuarios.py`)
- Crear test para creación y hasheo de passwords (RED).
- Como el código de negocio ya está implementado, las pruebas verificarán la funcionalidad existente (GREEN).
- Añadir tests para cambio de password y conteo de administradores.

## Paso 3: Catálogo (`test_catalogo.py`)
- Probar creación de categorías y productos.
- Probar el soft-delete (eliminación suave) y la validación que impide borrar categorías con productos activos.

## Paso 4: Órdenes (`test_ordenes.py`)
- Simular la creación de órdenes con productos variados.
- Probar el cálculo de subtotal y la correcta inserción en DB.
- Probar cambios de estado (`pending` -> `preparing` -> etc).

## Paso 5: Sesión (`test_session.py`)
- Simular login con varios usuarios.
- Asegurar que `ROLE_ACCESS` funciona como se espera para admins y cajeros.

## Paso 6: Verificación Final
- Ejecutar `python run_tests.py` y comprobar que todos los tests estén en OK.
