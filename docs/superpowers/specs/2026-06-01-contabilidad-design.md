# Diseño del Módulo Contable (Ingresos y Egresos)

Este documento detalla el plan y las opciones de diseño para implementar el módulo contable en Pizzas Pastra, cumpliendo con la regla de Superpowers de presentar un diseño antes de escribir código.

## 1. Opciones de Diseño (Enfoques)

Para el módulo de contabilidad de un punto de venta (pizzería), propongo las siguientes aproximaciones:

### Opción 1: Libro Mayor Simple (Manual)
- **Descripción**: Una vista sencilla donde el administrador registra manualmente cada "Ingreso" y "Egreso", indicando monto, fecha y descripción.
- **Pros**: Muy fácil y rápido de construir. Muy simple para el cliente.
- **Contras**: No se integra automáticamente con las ventas que ya suceden en el Punto de Venta. Requiere doble trabajo por parte del administrador (registrar las ventas en el POS y luego sumarlas al módulo contable).

### Opción 2: Contabilidad Categorizada y Automática (Recomendada)
- **Descripción**: 
  - Las órdenes completadas en el POS automáticamente generan un registro de "Ingreso" en la contabilidad (por el total de la orden).
  - El administrador puede registrar "Egresos" (gastos) manualmente y asignarlos a categorías (ej. Insumos, Nómina, Servicios Públicos).
  - El módulo muestra un resumen de caja: Total Ingresos (Ventas POS + Otros ingresos) - Total Egresos = Balance.
- **Pros**: Automatiza el flujo de ingresos principales. Permite saber exactamente en qué se gasta el dinero mediante las categorías.
- **Contras**: Ligeramente más complejo de implementar (requiere interceptar el cierre de órdenes para registrar el ingreso).

### Opción 3: Contabilidad de Partida Doble (Doble Asiento)
- **Descripción**: Un sistema contable formal (Débito/Crédito, cuentas contables complejas, conciliación bancaria).
- **Pros**: Robustez financiera total.
- **Contras**: Excesivamente complejo e innecesario para el modelo de negocio de una pizzería (Over-engineering / Viola YAGNI). 

Mi recomendación es la Opción 2.

## 2. Preguntas para el Usuario (Feedback Requerido)

1. ¿Estás de acuerdo con la Opción 2 (Contabilidad Categorizada y Automática)?
2. ¿Deseas que cada orden del POS genere un registro individual en contabilidad, o prefieres un único registro de "Cierre de Caja Diario" que sume todas las ventas del día?
3. Entiendo que solo el usuario con rol `admin` debería tener acceso a este módulo. ¿Es correcto?
