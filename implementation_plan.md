# Implementación de Instalador y Renombrado a FastBite POS

Este plan detalla los pasos para cambiar el nombre del proyecto a "FastBite POS" y trasladar la configuración inicial (nombre del negocio, usuario admin) al instalador creado con Inno Setup.

## User Review Required

> [!WARNING]
> **Consideración de Experiencia de Usuario (UX):**
> Trasladar la configuración inicial al instalador de Inno Setup significa que la recolección de datos se hará con la interfaz clásica de instaladores de Windows (estilo "siguiente, siguiente"). 
> Actualmente, la aplicación tiene un `SetupWizard` con un diseño moderno (modo oscuro, íconos, validaciones en tiempo real). 
> **Recomendación:** Muchos sistemas modernos instalan los archivos primero de forma silenciosa o rápida, y dejan que el "Primer Inicio" de la aplicación maneje la configuración inicial para mantener una experiencia premium. 
> 
> Si apruebas este plan, implementaré la recolección de datos en Inno Setup (escribiendo un archivo INI temporal que la app leerá). Si prefieres mantener la pantalla de bienvenida actual dentro de la app (solo para el primer uso) y que el instalador solo copie archivos, házmelo saber.

## Open Questions

- ¿Deseas mantener la recolección de datos en el instalador (Inno Setup) a pesar de que la interfaz será más clásica, o prefieres que el instalador solo instale y la app siga mostrando su pantalla de bienvenida moderna en el primer inicio?

## Proposed Changes

### Renombrado a FastBite POS

#### [MODIFY] config.py
- Cambiar `APP_NAME = "Pizzas Pastra"` a `"FastBite POS"`
- Cambiar las rutas de base de datos de `.pizzaspastra` a `.fastbitepos`

#### [MODIFY] build.py
- Actualizar el script para usar `FastBitePOS.spec`

#### [NEW] FastBitePOS.spec
- Renombrar y actualizar el archivo `.spec` para generar `FastBitePOS.exe`.
#### [DELETE] PizzasPastra.spec
- Eliminar el spec antiguo.

### Integración de Setup con Inno Setup (Si decides moverlo al instalador)

#### [NEW] fastbite_setup.iss
- Script de Inno Setup.
- Incluirá código en **Pascal Script** para crear páginas personalizadas (CustomPages) que pidan:
  - Nombre del Negocio
  - Usuario Administrador
  - Contraseña
- Al finalizar la instalación, el script escribirá estos datos en un archivo `setup_init.ini` en la carpeta de instalación (o en `%APPDATA%\FastBitePOS`).

#### [MODIFY] main.py
- Modificar la lógica de inicio:
  - Si no hay usuarios en la DB:
    - Buscar si existe `setup_init.ini`.
    - Si existe, leer los datos, poblar la base de datos (crear admin, guardar configuración del negocio), y luego **eliminar** `setup_init.ini` por seguridad.
    - Si no existe (ej. ejecución en modo desarrollo), mostrar el `SetupWizard` normal como respaldo.

## Verification Plan

### Manual Verification
1. Generar el ejecutable usando `build.py`.
2. Compilar el archivo `fastbite_setup.iss` usando Inno Setup Compiler.
3. Ejecutar el instalador `FastBite_Setup.exe`.
4. Llenar los datos en el instalador.
5. Iniciar FastBite POS desde el acceso directo.
6. Verificar que el login acepte el usuario y contraseña ingresados en el instalador, y que el nombre del negocio se muestre correctamente.
