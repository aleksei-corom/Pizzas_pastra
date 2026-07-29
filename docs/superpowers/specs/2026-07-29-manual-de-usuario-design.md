# Design Spec: Manual de Usuario FastBite POS

- **Fecha**: 2026-07-29
- **Proyecto**: FastBite POS (Pizzas Pastra)
- **Documento objetivo**: `docs/MANUAL_DE_USUARIO.md`
- **Enfoque**: Opción A (Estructurado por Roles)

## Resumen del Proyecto

FastBite POS es un sistema de Punto de Venta (POS) para negocios de comida rápida y pizzerías desarrollado con Python 3.10+, PySide6 y SQLite. Ofrece módulos para toma de pedidos, pantalla de cocina (KDS), envíos a domicilio, catálogo de productos/variantes/combos, gestión de usuarios/roles, contabilidad de caja, reportes y ajustes de impresora térmica ESC/POS.

## Estructura del Documento `docs/MANUAL_DE_USUARIO.md`

### 1. Sección General: Introducción y Primeros Pasos
- Bienvenida e Instalación/Inicio
- Asistente de Configuración Inicial (Setup Wizard)
- Inicio de Sesión y Autenticación (Credenciales / PIN)

### 2. Módulo I: Guía del Cajero y Operador de Ventas
- Apertura de Turno y Caja Inicial
- Toma de Órdenes en POS (Categorías, Variantes, Combos, Notas Especiales)
- Tipos de Pedido (Comer Aquí, Llevar, Domicilio)
- Proceso de Cobro (Efectivo, Tarjeta, Transferencia, Pago Mixto) e Impresión de Ticket
- Gestión de Domicilios y Asignación de Repartidores
- Historial de Órdenes y Devoluciones
- Movimientos de Caja y Arqueo / Cierre de Turno

### 3. Módulo II: Guía del Personal de Cocina (KDS) y Repartidores
- Pantalla de Cocina (KDS) en tiempo real
- Flujo de Estados (Pendiente -> En Preparación -> Listo)
- Tablero de Despacho y Repartidores (Asignación y Marcado de Entregado)

### 4. Módulo III: Guía del Administrador
- Administración de Menú (Categorías, Productos, Variantes, Combos)
- Gestión de Usuarios, Roles y PINs
- Contabilidad General y Cierres Históricos
- Reportes y Gráficos de Ventas
- Configuración del Sistema (Datos de la Empresa, Impresora ESC/POS / Windows, Apariencia, Backup DB)

### 5. Módulo IV: Preguntas Frecuentes y Solución de Problemas (Troubleshooting)
- Fallas de Impresión
- Olvido de PIN / Credenciales
- Descuadres de Caja
- Recuperación ante fallos eléctricos o del sistema
