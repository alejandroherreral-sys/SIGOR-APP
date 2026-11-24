# SIGOR — Sistema de Gestión Operativa de Restaurante

> **De procesos manuales a un sistema integrado:** conecta la atención en sala, el inventario en vivo, las ventas del día, la asistencia del personal y la auditoría en una sola herramienta.

---

## Descripción general

**SIGOR** es un sistema diseñado para un restaurante mediano que opera de forma manual, donde mesas, comensales, insumos y pedidos cambian de manera constante. La información fluye desde que el cliente se sienta y se atiende en sala hasta que el pedido avanza, se descuenta el inventario y se registra la venta.

## Problemática que resuelve

* **Causas:**
  * Registro manual de pedidos y de la ocupación de mesas, en papel o de memoria.
  * Sin comunicación en tiempo real entre las mesas y el almacén.
  * Ningún sistema descuenta el inventario al registrar una venta.
* **Efectos:**
  * Demoras, cruce de información y errores en la entrega de platos.
  * Descuadres de inventario: se ofrecen platos sin ingredientes.
  * Estrés del personal e insatisfacción de clientes.

## Usuarios y control por roles

SIGOR exige autenticación para acceder a los módulos y aplica control por roles para que cada perfil vea y use solo lo que le corresponde:

* **Acceso seguro y auditoría:**
  * Registro con usuario, contraseña, rol y código de seguridad de 4 dígitos.
  * Inicio de sesión validado: cada rol ve solo lo que le corresponde.
  * Cada ingreso queda registrado con fecha y hora para auditoría.
* **Mesero (usuario operativo):**
  * Atiende al cliente de forma directa a un ritmo dinámico en las horas de mayor tráfico.
  * Registra rápido qué mesas están ocupadas, cuántos comensales hay y qué platos pidieron, sin perder movilidad.
* **Administrador / Jefe de almacén (usuario de gestión):**
  * Responsable de la logística y la rentabilidad con un perfil más analítico.
  * Revisa qué insumos se agotan a medida que entran los pedidos para decidir compras y evitar el desabastecimiento, además de gestionar ventas, asistencia y auditoría.

## Módulos y funcionalidades

| Módulo | Rol | Funciones |
| :--- | :--- | :--- |
| **Mesas y pedidos** | Mesero / Administrador | Consulta estado de cada mesa (`Libre` / `Ocupada`), comensales, total actualizado y detalle del pedido (`Producto`, `Cant.`, `Precio`, `Subtotal`), con opciones para agregar al pedido, quitar línea y cobrar y liberar. |
| **Inventario** | Administrador | Muestra productos, precio, stock y estado (`OK` / `Stock bajo`), y permite crear, guardar, eliminar y reabastecer productos descontando unidades conforme entran pedidos. |
| **Ventas del día** | Administrador | Registra ventas de hoy (`Hora`, `Mesa`, `Total`, `Detalle`), muestra el total recaudado y resume las unidades vendidas por producto. |
| **Asistencia y auditoría** | Administrador | Gestiona el registro de asistencia del personal (`Trabajador`, `Fecha y hora`, `Estado` como `Presente` o `Tarde`, registrar presente, editar y eliminar) y consulta desde consola la auditoría de sesiones (`usuario`, `rol`, `fecha y hora` de cada ingreso). |

## Cierre y enfoque del sistema

* **Todo conectado:** mesas, pedidos, inventario y ventas comparten la misma información.
* **Control por rol:** meseros y administradores usan solo las funciones que les corresponden.
* **Un backend, dos interfaces:** la misma lógica funciona en la consola y en la aplicación gráfica.

## Integrantes y curso

* **Integrantes:**
  * Juan Camilo Cano Zaraza
  * Alejandro Herrera Lozano
  * Andrés Felipe Rojas Díaz
  * Breyner Stiven Soto
* **Asignatura:** Algoritmia y Programación — Universidad Autónoma de Occidente 
