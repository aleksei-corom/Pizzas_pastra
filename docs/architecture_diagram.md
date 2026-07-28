# Pizzas Pastra POS - Architecture Diagram

## Overview

Pizzas Pastra is a Point of Sale (POS) system built with PySide6 (Qt) and SQLite, designed for restaurant and food service management. It features role-based access control, thermal printing support, and a modular architecture.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         main.py (Entry Point)                   │
│  - App initialization                                            │
│  - Database setup & seeding                                       │
│  - Login loop (LoginView → MainWindow → Logout)                   │
│  - First-run setup wizard                                         │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                        config.py                                  │
│  - Global configuration (business info, currency, tax)         │
│  - Paths (DB location, APPDATA)                                  │
│  - Order types & status constants                                │
│  - Printer settings                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layered Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Presentation Layer                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  views/                                                   │  │
│  │  ├── main_window.py      (Main container with sidebar)    │  │
│  │  ├── login_view.py       (Authentication)                │  │
│  │  ├── setup_wizard.py     (First-time setup)               │  │
│  │  ├── pos_view.py         (Point of Sale)                  │  │
│  │  ├── dashboard_view.py   (Analytics & charts)            │  │
│  │  ├── menu_view.py        (Menu management)                │  │
│  │  ├── ordenes_view.py     (Order management)               │  │
│  │  ├── delivery_view.py    (Delivery management)            │  │
│  │  ├── kds_view.py         (Kitchen Display System)          │  │
│  │  ├── reportes_view.py    (Reports)                         │  │
│  │  ├── contabilidad_view.py (Accounting)                    │  │
│  │  ├── ajustes_view.py     (Settings)                        │  │
│  │  └── usuarios_view.py    (User management)                 │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  views/components/          (Reusable UI widgets)          │  │
│  │  ├── sidebar.py             (Navigation sidebar)           │  │
│  │  ├── order_panel.py          (Current order panel)          │  │
│  │  ├── product_card.py         (Product display card)         │  │
│  │  ├── combo_card.py           (Combo display card)           │  │
│  │  ├── payment_dialog.py       (Payment processing)           │  │
│  │  ├── variant_dialog.py       (Product variant selection)    │  │
│  │  ├── combo_dialog.py         (Combo builder)                │  │
│  │  ├── user_dialog.py          (User CRUD dialog)             │  │
│  │  ├── repartidor_dialog.py    (Delivery driver dialog)      │  │
│  │  ├── search_bar.py           (Search input)                  │  │
│  │  ├── card_widget.py          (Generic card container)       │  │
│  │  ├── chart_widgets.py        (Charts: bar, donut, trend)    │  │
│  │  ├── status_badge.py         (Status indicators)            │  │
│  │  ├── modern_messagebox.py    (Custom message boxes)          │  │
│  │  └── loading_spinner.py      (Loading indicator)             │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  views/layouts/            (Layout helpers)                 │  │
│  │  └── form_helpers.py       (Form layout utilities)         │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Business Logic Layer                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  utils/session.py          (Session management)              │  │
│  │  - User authentication & authorization                     │  │
│  │  - Role-based access control (admin/cajero)                  │  │
│  │  - User preferences (per-user printer, etc.)                 │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  utils/printer.py          (ESC/POS thermal printing)        │  │
│  │  - Windows printer detection (win32print)                   │  │
│  │  - ESC/POS command generation                              │  │
│  │  - Receipt formatting (58mm/80mm)                           │  │
│  │  - Code page support (CP437/CP850)                          │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  utils/backup_manager.py  (Database backups)               │  │
│  │  - Daily automatic backups                                 │  │
│  │  - Backup rotation                                          │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  utils/app_logging.py      (Logging setup)                 │  │
│  │  - File logging to logs/ directory                         │  │
│  │  - Exception hook for crash reporting                      │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Data Access Layer                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  database/db_manager.py   (SQLite singleton)               │  │
│  │  - Thread-safe connection pooling                          │  │
│  │  - CRUD operations for all entities                         │  │
│  │  - Database migrations                                       │  │
│  │  - Configuration management                                 │  │
│  │  - User preferences storage                                 │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  database/models.py        (Dataclass models)               │  │
│  │  - Categoria, Producto, ProductoVariante                   │  │
│  │  - ProductoIngrediente, Combo, ComboItem                   │  │
│  │  - Orden, OrdenItem, Repartidor                             │  │
│  │  - Usuario, Transaccion                                     │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  database/seed_data.py    (Initial data)                   │  │
│  │  - Default categories (Pizza, Bebida, etc.)                 │  │
│  │  - Sample products                                         │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Data Layer                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  SQLite Database (pizzas_pastra.db)                        │  │
│  │  Tables: categorias, productos, ordenes, orden_items,      │  │
│  │          configuracion, usuarios, transacciones,           │  │
│  │          user_preferences, repartidores,                    │  │
│  │          producto_variantes, producto_ingredientes,          │  │
│  │          combos, combo_items                                 │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Application Flow

### Startup Flow

```
main.py
  │
  ├─→ Setup logging
  ├─→ Run daily backup
  ├─→ Initialize DatabaseManager (singleton)
  ├─→ Create tables (if not exist)
  ├─→ Seed initial data
  ├─→ Load config from DB into config.py globals
  │
  ├─→ Check if first run (no users)
  │   ├─→ YES: Run SetupWizard or read setup_init.ini
  │   │         (create admin user, business config)
  │   └─→ NO: Continue to login
  │
  └─→ Login Loop:
      ├─→ Show LoginView
      ├─→ User authenticates
      ├─→ Session.login(user)
      ├─→ Show MainWindow (with role-filtered sidebar)
      ├─→ User works in app
      ├─→ User logs out → Session.logout()
      └─→ Loop back to LoginView
```

### Main Window Navigation

```
MainWindow
  │
  ├─→ Sidebar (role-filtered navigation)
  │   ├─→ Admin: dashboard, pos, menu, ordenes, domicilios,
  │   │         cocina, reportes, contabilidad, ajustes, usuarios
  │   └─→ Cajero: pos, ordenes, domicilios, cocina
  │
  └─→ QStackedWidget (views)
      ├─→ DashboardView    (stats, charts, recent orders)
      ├─→ POSView          (product grid, order panel, payment)
      ├─→ MenuView         (CRUD products, categories, combos)
      ├─→ OrdenesView      (order list, status management)
      ├─→ DeliveryView     (delivery orders, driver assignment)
      ├─→ KitchenDisplayView (KDS for kitchen staff)
      ├─→ ReportesView     (sales reports, exports)
      ├─→ ContabilidadView (income/expense tracking)
      ├─→ AjustesView      (business config, printer setup)
      └─→ UsuariosView     (user CRUD, role management)
```

---

## Database Schema

### Core Tables

```
categorias
  ├── id (PK)
  ├── nombre
  ├── icono
  ├── orden
  └── activa

productos
  ├── id (PK)
  ├── nombre
  ├── descripcion
  ├── precio
  ├── categoria_id (FK → categorias)
  ├── disponible
  ├── icono
  └── tiene_variantes

producto_variantes
  ├── id (PK)
  ├── producto_id (FK → productos)
  ├── nombre (e.g., "Personal", "Mediana")
  ├── precio_adicional
  └── orden

producto_ingredientes
  ├── id (PK)
  ├── producto_id (FK → productos, nullable)
  ├── nombre
  ├── precio_adicional
  ├── categoria
  └── activo

combos
  ├── id (PK)
  ├── nombre
  ├── descripcion
  ├── precio_total
  ├── ahorro
  ├── icono
  ├── activo
  └── fecha_creacion

combo_items
  ├── id (PK)
  ├── combo_id (FK → combos)
  ├── producto_id (FK → productos)
  ├── producto_nombre
  ├── cantidad
  └── precio_individual

ordenes
  ├── id (PK)
  ├── numero (unique)
  ├── tipo (local/takeout/delivery)
  ├── estado (pending/preparing/ready/delivered/cancelled)
  ├── subtotal
  ├── impuesto
  ├── total
  ├── cliente_nombre
  ├── notas
  ├── fecha_creacion
  ├── fecha_actualizacion
  ├── direccion (delivery)
  ├── telefono_contacto (delivery)
  ├── costo_delivery (delivery)
  ├── tiempo_estimado (delivery)
  └── repartidor_id (FK → repartidores, delivery)

orden_items
  ├── id (PK)
  ├── orden_id (FK → ordenes, CASCADE)
  ├── producto_id (FK → productos)
  ├── producto_nombre
  ├── cantidad
  └── precio_unitario

repartidores
  ├── id (PK)
  ├── nombre
  ├── telefono
  ├── vehiculo (moto/carro/bicicleta/pie)
  ├── activo
  └── fecha_creacion

usuarios
  ├── id (PK)
  ├── username (unique)
  ├── password_hash
  ├── salt
  ├── nombre_completo
  ├── rol (admin/cajero)
  ├── activo
  └── fecha_creacion

user_preferences
  ├── user_id (FK → usuarios, PK part 1)
  ├── clave (PK part 2)
  └── valor

transacciones
  ├── id (PK)
  ├── tipo (ingreso/egreso)
  ├── monto
  ├── descripcion
  ├── fecha
  ├── categoria
  └── referencia_orden_id (FK → ordenes)

configuracion
  ├── clave (PK)
  └── valor
```

---

## Key Design Patterns

### Singleton Pattern
- `DatabaseManager` - Thread-safe SQLite connection
- `Session` - User session state

### Model-View Separation
- Data models in `database/models.py` (dataclasses)
- Views in `views/` (PySide6 widgets)
- Business logic in views and utils

### Role-Based Access Control
- `Session.ROLE_ACCESS` defines module permissions
- Sidebar filters navigation based on user role
- Views check `session.has_access(module_name)`

### Signal-Slot Pattern (Qt)
- Sidebar navigation signals
- Order panel signals (order_confirmed)
- Payment dialog signals
- Logout signals

---

## Key Dependencies

- **PySide6** - Qt for Python (GUI framework)
- **SQLite** - Embedded database (Python stdlib)
- **pywin32** - Windows printer access (ESC/POS)
- **dataclasses** - Data models (Python 3.7+)

---

## File Structure

```
Pizzas_pastra/
├── main.py                 # Entry point
├── config.py               # Global configuration
├── requirements.txt        # Dependencies
├── build.py                # PyInstaller build script
├── FastBitePOS.spec        # PyInstaller spec file
├── fastbite_setup.iss      # Inno Setup installer script
│
├── database/
│   ├── __init__.py
│   ├── db_manager.py       # SQLite operations
│   ├── models.py           # Dataclass models
│   └── seed_data.py        # Initial data
│
├── views/
│   ├── __init__.py
│   ├── main_window.py      # Main container
│   ├── login_view.py       # Authentication
│   ├── setup_wizard.py     # First-time setup
│   ├── pos_view.py         # Point of Sale
│   ├── dashboard_view.py   # Dashboard
│   ├── menu_view.py        # Menu management
│   ├── ordenes_view.py     # Orders
│   ├── delivery_view.py    # Delivery
│   ├── kds_view.py         # Kitchen Display
│   ├── reportes_view.py    # Reports
│   ├── contabilidad_view.py # Accounting
│   ├── ajustes_view.py     # Settings
│   ├── usuarios_view.py    # Users
│   ├── components/         # Reusable widgets
│   │   ├── sidebar.py
│   │   ├── order_panel.py
│   │   ├── product_card.py
│   │   ├── combo_card.py
│   │   ├── payment_dialog.py
│   │   ├── variant_dialog.py
│   │   ├── combo_dialog.py
│   │   ├── user_dialog.py
│   │   ├── repartidor_dialog.py
│   │   ├── search_bar.py
│   │   ├── card_widget.py
│   │   ├── chart_widgets.py
│   │   ├── status_badge.py
│   │   ├── modern_messagebox.py
│   │   └── loading_spinner.py
│   ├── layouts/            # Layout helpers
│   │   └── form_helpers.py
│   └── themes/             # Theme definitions
│
├── utils/
│   ├── session.py          # Session management
│   ├── printer.py          # ESC/POS printing
│   ├── backup_manager.py   # Database backups
│   └── app_logging.py      # Logging setup
│
├── tests/                  # Unit tests
│   ├── test_catalogo.py
│   ├── test_contabilidad.py
│   ├── test_ordenes.py
│   ├── test_session.py
│   └── test_usuarios.py
│
├── docs/                   # Documentation
│   └── superpowers/
│
├── assets/                 # Static assets
├── logs/                   # Application logs
├── .venv/                  # Virtual environment
└── pizzas_pastra.db        # SQLite database (runtime)
```

---

## Technology Stack Summary

- **Language**: Python 3.x
- **GUI Framework**: PySide6 (Qt6)
- **Database**: SQLite (thread-safe singleton)
- **Printing**: ESC/POS via win32print
- **Architecture**: Layered (Presentation → Business Logic → Data Access → Data)
- **Design Patterns**: Singleton, MVC-like, Signal-Slot
- **Deployment**: PyInstaller + Inno Setup (Windows installer)
