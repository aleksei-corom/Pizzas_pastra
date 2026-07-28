# FastBite POS (anteriormente Pizzas Pastra) 🍕

FastBite POS es un completo sistema de Punto de Venta (Point of Sale) diseñado originalmente para pizzerías y adaptable a diversos restaurantes y negocios de comida rápida. Su diseño amigable e intuitivo está pensado para optimizar el flujo de trabajo, reducir tiempos de espera y mejorar la experiencia tanto de tus empleados como de tus clientes.

## 🚀 Características Principales

*   **Gestión de Órdenes y Entregas**: Soporte para tomar órdenes en mostrador o para envío (delivery). Interfaz dedicada (Kitchen Display System - KDS) para visualizar, priorizar y marcar las órdenes preparadas.
*   **Gestión de Catálogo**: Administración visual y eficiente de productos, combos y variantes (por ej. tamaños de pizza, tipos de masa) y categorías.
*   **Gestión de Usuarios y Roles**: Manejo de permisos para distintos roles (Admin, Cajero) y soporte seguro de autenticación local.
*   **Gestión de Repartidores**: Control de estado de repartidores y asignación eficaz de entregas.
*   **Reportes y Estadísticas**: Visualización de métricas esenciales (ventas del día, órdenes completadas) para ayudar en la toma de decisiones.
*   **Impresión de Recibos**: Integración con impresoras térmicas (protocolo ESC/POS y compatibilidad local en Windows) para emitir tickets rápidamente.
*   **Interfaz Moderna**: Interfaz gráfica construida con PySide6, utilizando estilos y widgets modernos con soporte de modo claro/oscuro (ajustable) e iconos representativos.

## 🛠️ Tecnologías

*   **Lenguaje**: Python 3.10+
*   **Interfaz Gráfica (GUI)**: PySide6 (Qt para Python)
*   **Base de Datos**: SQLite (almacenamiento local, eficiente y sin configuración de servidor)
*   **Impresión**: Integración con `win32print` para soporte de impresión en sistemas Windows y compatibilidad con ESC/POS.

## 📦 Instalación y Configuración Local

1.  **Clona el repositorio:**
    ```bash
    git clone https://github.com/aleksei-corom/Pizzas_pastra.git
    cd Pizzas_pastra
    ```

2.  **Crea y activa un entorno virtual (Recomendado):**
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
    *Nota: Si es la primera vez que inicias la aplicación, se mostrará un asistente (Setup Wizard) para crear la cuenta de administrador y configurar detalles iniciales del negocio.*

## 🧪 Pruebas (Testing)

El proyecto cuenta con una robusta suite de pruebas unitarias creadas utilizando la librería estándar `unittest`. 

Para ejecutar los tests, simplemente corre en la consola:
```bash
python run_tests.py
```

*Las pruebas incluyen mocks para eludir la interacción visual con diálogos de interfaz, logrando que el test suite pueda ejecutarse en entornos Headless (como GitHub Actions).*

## 📄 Licencia

Este proyecto está bajo la Licencia **MIT**. Consulta el archivo `LICENSE` para más detalles.
