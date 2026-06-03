# Diseño de la Suite de Pruebas Unitarias (Test Suite)

Para asegurar la robustez de Pizzas Pastra, propongo crear una suite de pruebas unitarias estructurada que cubra la lógica de negocio y el manejo de base de datos. 

## 1. Opciones de Diseño (Enfoques)

### Opción 1: Suite Completa con Pytest + Cobertura
- **Descripción**: Migraríamos los tests actuales a `pytest`, instalaríamos librerías como `pytest-qt` (para probar UI) y `pytest-cov` (para medir cobertura).
- **Pros**: Muy moderno, permite probar la interfaz gráfica y medir qué porcentaje del código está cubierto por tests.
- **Contras**: Requiere instalar y configurar dependencias adicionales. Probar interfaces gráficas de PySide6 es complejo y a menudo frágil ante cambios mínimos visuales.

### Opción 2: Pruebas Unitarias de Lógica y BD con `unittest` (Recomendada)
- **Descripción**: Utilizar el módulo nativo `unittest` de Python (que ya usamos para contabilidad) para probar exhaustivamente el acceso a datos (`db_manager.py`) y la lógica de negocio (`session.py`, cálculos de totales, etc.), dejando la UI a pruebas manuales.
- **Módulos a probar**:
  1. **Usuarios y Autenticación**: `test_usuarios.py` (crear, editar, hashear passwords, login, roles).
  2. **Categorías y Productos**: `test_catalogo.py` (crear, soft-delete, disponibilidad, búsqueda).
  3. **Órdenes y Ventas**: `test_ordenes.py` (crear, subtotales, impuestos, estados de orden).
  4. **Sesión**: `test_session.py` (roles y permisos, login/logout).
- **Pros**: Cero dependencias adicionales (usa la biblioteca estándar), tests rápidos (usan BD en memoria `:memory:`), máxima estabilidad al enfocarse en la lógica core y no en la interfaz gráfica.
- **Contras**: No se prueba automáticamente el comportamiento de los botones de la interfaz visual.

Mi recomendación es la Opción 2. En aplicaciones de escritorio pequeñas/medianas, asegurar que la base de datos y la lógica interna no fallen (TDD) es el 90% del éxito.

---

## 2. Preguntas para el Usuario (Feedback Requerido)

1. ¿Estás de acuerdo con seguir la Opción 2 (enfocarnos en probar la Base de Datos y Lógica usando `unittest` en memoria) para mantenerlo simple y libre de nuevas dependencias?
2. ¿Existe algún otro módulo crítico o función específica (ej. creación de backups) que desees que esté cubierto por las pruebas de forma prioritaria?
