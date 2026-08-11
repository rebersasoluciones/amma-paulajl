# Fisioterapia – Gestión de Grupos y Clases (Odoo 19)

Módulo profesional para clínicas de fisioterapia que trabajan por **grupos/clases**,
con **suscripciones mensuales**, **cobros online** y un **portal para pacientes al
estilo WODBUSTER**.

## Funcionalidades

### Backend (personal de la clínica)
- **Pacientes**: alta rápida (nombre, teléfono, correo) integrada en *Contactos*
  (`is_physio_patient`). Botón inteligente con sus suscripciones.
- **Grupos**: horario semanal, duración, capacidad por clase y cuota mensual.
  Generación automática de las clases del periodo (asistente + cron).
- **Clases**: vistas *calendario / kanban / lista*. Ocupación en tiempo real
  (plazas ocupadas / libres) y lista de pacientes por clase con control de
  asistencia (asistió / no asistió).
- **Suscripciones**: vinculan paciente ↔ grupo. Al activarse crean una
  **suscripción nativa de Odoo** (`sale_subscription`) que gestiona la
  **facturación recurrente** (fecha de inicio, posición fiscal, condiciones de
  pago, tarifa) y el pago sobre la factura. Estados borrador / activa / pausada /
  cancelada, sincronizados con la suscripción nativa. Cambio de grupo con un
  asistente. Tope de clases al mes por paciente.
- **Cobros**: al facturar se envía un correo con un botón **“Pagar ahora”** que
  lleva al portal para pagar con los métodos de pago activos. Panel *Cobros* para
  **generar enlaces de pago al momento** o **registrar pago en efectivo/banco**.

### Portal del paciente (estilo WODBUSTER)
Ruta `/my/physio` (tarjeta también en `/my/home`):
- **Plaza asignada automática**: el paciente aparece ya apuntado a todas las clases
  de su grupo, sin tener que reservar (opción `auto_enroll` del grupo).
- Ver a qué **grupo(s)** está suscrito y su horario habitual.
- **“No puedo asistir”**: anula su asistencia a un día y **libera su plaza** para
  que otro paciente pueda ocuparla.
- Ver **clases disponibles** (con las **plazas libres** de cada una) y **apuntarse**,
  incluidas clases de **otros grupos** cuando el destino lo permite y hay hueco.
- **Antelación mínima** configurable por grupo (por defecto **24h**): fuera de ese
  plazo ya no se puede anular ni apuntarse desde el portal.
- Ver y **pagar** las cuotas pendientes (pago **nativo** sobre la factura).

> **Cuota por paciente**: la cuota mensual es la del grupo por defecto, pero cada
> suscripción tiene su propio importe editable para pacientes con condiciones
> especiales.

## Modelo de datos
| Modelo | Descripción |
|--------|-------------|
| `physio.group` | Grupo con horario, capacidad y cuota |
| `physio.group.schedule` | Franja del horario semanal |
| `physio.session` | Clase concreta (fecha/hora) con control de plazas |
| `physio.booking` | Reserva / asistencia de un paciente a una clase |
| `physio.membership` | Suscripción paciente ↔ grupo (respaldada por una suscripción nativa) |
| `sale.order` (ext.) | Suscripción nativa de facturación + enlace al grupo/paciente |
| `res.partner` (ext.) | Marca de paciente y sus suscripciones |
| `account.move` (ext.) | Enlace a la suscripción + acciones de cobro |

## Configuración recomendada
1. **Facturación**: instala *Contabilidad* o *Facturación* y configura un diario de
   ventas.
2. **Pagos online**: en *Ajustes → Facturación/Pagos*, activa al menos un
   proveedor de pago y **“Pago desde el portal”** para que funcione el botón de la
   plantilla de correo.
3. **Efectivo**: crea un diario de tipo *Efectivo* para registrar pagos en mano.

## Seguridad
- **Fisioterapia / Recepción**: gestión operativa (pacientes, clases, cobros).
- **Fisioterapia / Responsable**: además configuración (grupos, precios).
- **Portal**: cada paciente sólo ve sus suscripciones, reservas y las clases
  disponibles (reglas de registro incluidas).

## Automatismos (cron)
- *Facturar suscripciones vencidas* (diario): genera la factura y envía el cobro.
- *Generar clases del periodo* (semanal): crea las clases de las próximas semanas
  a partir del horario de cada grupo.

Licencia: LGPL-3. Autor: Rebersa Soluciones.
