# FastBite POS (v1.1.0) 🍕

FastBite POS es un completo sistema de Punto de Venta (Point of Sale), Gestión de Cocina (KDS), Fidelización de Clientes y Control Contable diseñado para restaurantes de comida rápida, pizzerías y establecimientos gastronómicos. Su diseño amigable e intuitivo optimiza el flujo de trabajo, reduce tiempos de espera y mejora la rentabilidad del negocio.

---

## 🚀 Características Principales

*   **💎 CRM & Fidelización de Clientes (Novedad v1.1.0)**: Búsqueda rápida por teléfono durante la venta, acumulación automatizada de puntos por compras, historial de visitas y catálogo de premios canjeables.
*   **🧑‍🍳 Analizador de Costos y Recetas (Novedad v1.1.0)**: Construcción de recetas con desglose de insumos, cálculo automatizado del costo real por porción, análisis de márgenes de ganancia y recomendaciones de precio.
*   **🧠 Asistente Inteligente de Ventas (Novedad v1.1.0)**: Motor analítico 100% local que identifica horas pico, productos estrella, patrones de demanda y alertas de reposición de insumos sin depender de APIs externas.
*   **Gestión de Órdenes y Delivery**: Soporte para comer en local, para llevar y servicio a domicilio. Pantalla dedicada de cocina (Kitchen Display System - KDS) con códigos de color según tiempo de espera.
*   **Gestión de Catálogo y Combos**: Administración de categorías, productos, variantes (tamaños, bordes de queso), adicionales y paquetes promocionales (combos).
*   **Seguridad y Control de Roles**: Autenticación rápida por PIN de 4 dígitos o credenciales completas para administradores, cajeros, cocineros y repartidores.
*   **Arqueo de Caja y Contabilidad**: Control de aperturas/cierres de turno, registro de ingresos/egresos y reporte Z transparente (cuadre, sobrante o faltante).
*   **Impresión Térmica de Recibos**: Emisión automática de tickets para clientes y comandas de cocina vía impresoras térmicas ESC/POS y compatibilidad local en Windows.
*   **Interfaz Moderna en Modo Oscuro**: UI construida en PySide6 con componentes visuales adaptativos y estética minimalista.

---

## 🛠️ Tecnologías

*   **Lenguaje**: Python 3.10+
*   **Interfaz Gráfica (GUI)**: PySide6 (Qt para Python)
*   **Base de Datos**: SQLite (almacenamiento local thread-safe con migraciones automáticas)
*   **Impresión**: Integración con `win32print` y comandos directos ESC/POS.

---

## 📦 Instalación y Configuración Local

1.  **Clona el repositorio:**
    ```bash
    git clone https://github.com/aleksei-corom/Pizzas_pastra.git
    cd Pizzas_pastra
    ```

2.  **Crea y activa un entorno virtual:**
    ```bash
    python -m venv venv
    # En Windows:
    venv\Scripts\activate
    # En Linux/Mac:
    source venv/bin/activate
    ```

3.  **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Inicia la aplicación:**
    ```bash
    python main.py
    ```
    *Nota: En el primer inicio se desplegará el Asistente de Configuración Inicial (Setup Wizard) para definir el nombre del negocio, moneda, tasa de impuesto y cuenta de administrador.*

---

## 📚 Manual de Usuario

Consulta el manual de usuario ilustrado organizado por roles (Cajero, Cocinero, Repartidor, Administrador):
* 📖 [Manual de Usuario - FastBite POS](docs/MANUAL_DE_USUARIO.md)

---

## 🧪 Pruebas (Testing)

El proyecto cuenta con una amplia suite de más de 690 pruebas unitarias e integrales que cubren la capa de datos, lógica de negocio y componentes de interfaz.

Para ejecutar los tests:
```bash
python run_tests.py
```

---

## 💖 Apoya este Proyecto

Si este sistema te es útil o te ha ayudado a gestionar tu negocio de manera eficiente, por favor considera apoyar su desarrollo mediante **GitHub Sponsors**.

---

## 📄 Licencia

Este proyecto está bajo la Licencia **GNU AGPLv3** (GNU Affero General Public License v3.0).

Copyright (c) 2026 Alexis Corpas Romero - CORJAR Computers.
