# FastBite POS — Nuevos Módulos Diferenciadores

## Resumen de la implementación

Se agregan **3 módulos nuevos** que diferencian a FastBite POS de la competencia:

### 1. 💎 CRM & Fidelización (`clientes_view.py` + `cliente_service.py`)
Sistema de lealtad con búsqueda por teléfono, puntos acumulables, premios canjeables e historial de compras por cliente.

### 2. 🧑‍🍳 Analizador de Costos y Recetas (`costos_view.py` + `receta_service.py`)
Constructor de recetas con desglose de ingredientes, análisis de margen por producto, sugerencias de precios.

### 3. 🧠 Asistente Inteligente de Ventas (`asistente_view.py` + `asistente_service.py`)
Widget de inteligencia local que analiza patrones de ventas y sugiere acciones: reposición, promociones, horas pico, predicciones.

---

## Archivos nuevos (16 archivos)

### Base de datos
- `database/models.py` — Se agregan 4 dataclasses nuevos (Cliente, ClientePuntos, Receta, RecetaIngrediente)
- `database/db_manager.py` — Se agregan 4 tablas nuevas en migraciones
- `database/cliente_service.py` — Servicio CRUD + puntos + búsqueda por teléfono
- `database/receta_service.py` — Servicio CRUD + cálculos de costo y margen
- `database/asistente_service.py` — Motor de análisis de datos e insights
- `database/__init__.py` — Exporta nuevos servicios

### Vistas
- `views/clientes_view.py` — Vista completa CRM con búsqueda, registro, puntos
- `views/costos_view.py` — Vista de análisis de costos y recetas
- `views/asistente_view.py` — Vista del asistente inteligente con insights
- `views/components/cliente_dialog.py` — Diálogo de creación/edición de clientes
- `views/components/receta_dialog.py` — Diálogo de creación/edición de recetas
- `views/components/premio_dialog.py` — Diálogo de gestión de premios
- `views/components/insight_card.py` — Widget reutilizable para mostrar insights

### Integración
- `views/main_window.py` — Registra los 3 módulos nuevos en la navegación
- `views/components/sidebar.py` — Agrega los 3 items al menú de navegación
- `utils/session.py` — Agrega permisos por rol para los nuevos módulos
- `requirements.txt` — Sin cambios (no requiere dependencias nuevas)

---

## Instrucciones de instalación

1. Respaldar el proyecto actual
2. Copiar cada archivo a su ruta correspondiente (sobreescribir los modificados)
3. Al iniciar la app, las nuevas tablas se crean automáticamente (migración)
4. Los módulos aparecen en el sidebar: 💎 Clientes, 🧑‍🍳 Costos, 🧠 Asistente

## Notas técnicas

- Todas las consultas usan el patrón `row_to_model()` existente
- Los servicios siguen el patrón singleton de `DatabaseManager`
- Las vistas usan `create_page_header()` y `CardWidget` existentes
- Los colores se obtienen del tema activo via `th()`
- Compatible con el sistema de roles (admin ve todo, cajero ve POS + clientes básico)
