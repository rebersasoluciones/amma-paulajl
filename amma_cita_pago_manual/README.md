# Citas – Reserva manual con enlace de pago

Permite que el personal de la clínica reserve, **desde el backend**, una cita de
un tipo con *pago por adelantado*, generando el **pedido de venta** y el
**enlace de pago** para enviárselo al paciente. La cita aparece en el calendario
del profesional **sólo cuando se cobra** (o cuando alguien confirma el pedido a
mano).

No se emite factura antes del cobro: el flujo va por `sale.order`, no por
`account.move`, para no generar apuntes en SII/Verifactu de una cita que puede
no llegar a pagarse. El método nativo `calendar.booking._make_invoice_from_booking()`
(que sí factura) no se usa.

## Qué añade

Un único asistente, `appointment.manual.booking`, en **Citas → Agenda →
Reservar cita con pago**. Todo lo demás es mecanismo nativo de Odoo 19 EE:

| Paso | Quién lo hace |
|---|---|
| Reserva pendiente de pago (`calendar.booking` + `calendar.booking.line`) | este módulo, con los mismos valores que el formulario público |
| Comprobación del hueco | `calendar.booking._filter_unavailable_bookings()` (nativo) |
| Pedido y línea (`sale.order` / `sale.order.line` con `calendar_booking_ids`) | este módulo |
| Enlace de pago | asistente nativo `payment.link.wizard` (acción `sale.action_sale_order_generate_link`) |
| Confirmación del pedido al cobrar | `payment.transaction._check_amount_and_confirm_order()` (nativo) |
| Creación de la cita al confirmar | `sale.order._action_confirm()` → `calendar_booking_ids._make_event_from_paid_booking()` (nativo, de `website_appointment_sale`) |
| Limpieza de reservas caducadas | `calendar.booking._gc_calendar_booking` (nativo, autovacuum) |

## Requisitos de configuración

- El tipo de cita debe tener **Pago por adelantado** activado y un **producto de
  reserva**. Si no, el asistente bloquea con un aviso explicando dónde
  configurarlo (Citas → Tipos de cita).
- El usuario que reserva necesita permisos de **Citas** y de **Ventas** (crea un
  pedido). El asistente en sí está abierto al grupo *Citas / Usuario*.
- Para que el cobro confirme el pedido solo, tiene que haber un **proveedor de
  pago publicado** y el pedido tiene que llegar al cliente por el enlace.

## Cómo se usa

1. **Citas → Agenda → Reservar cita con pago**.
2. Paciente, tipo de cita, profesional (o recurso, según el tipo), inicio,
   duración y plazas.
3. *Confirmar y generar enlace de pago*: se crea la reserva y el pedido en
   borrador, y se abre el asistente nativo del enlace para copiarlo o enviarlo.
4. El paciente paga → el pedido se confirma → aparece la cita en el calendario
   del profesional. Si se prefiere, se puede confirmar el pedido a mano.

Si el paciente no paga nunca, no se crea ninguna cita y el pedido se queda en
borrador; las reservas viejas las limpia el autovacuum nativo.

Por defecto cada cita genera un pedido nuevo. En el campo *Añadir a este pedido*
se puede elegir un pedido en borrador ya existente del mismo paciente (por
ejemplo para cobrar varias citas de una vez).

## Cosas a tener en cuenta

- **El pedido exige pago en línea** (`require_payment`), así que sólo se confirma
  cuando lo cobrado llega al mínimo del pedido: por defecto el 100%, o el
  porcentaje de anticipo que tenga configurado el pedido. Sin esa marca,
  cualquier importe parcial pagado desde el enlace confirmaría el pedido y
  crearía la cita.
- **El hueco no queda bloqueado hasta el cobro.** Es el comportamiento nativo:
  las reservas pendientes de pago (`calendar.booking`) no cuentan como ocupación,
  así que dos pedidos sin pagar pueden apuntar al mismo hueco. La disponibilidad
  se vuelve a comprobar al confirmar el pedido y, si el hueco se ha ocupado, la
  cita no se crea y queda registrado en el chatter del pedido.
- **Capacidad**: se calcula igual que en el flujo público
  (`min(capacidad restante, plazas pedidas, capacidad por usuario)`), incluida la
  particularidad nativa de que `user_capacity` sólo actúa como tope real cuando
  el tipo de cita gestiona capacidad.
- **Citas por recurso**: el asistente permite elegir **un** recurso. El
  formulario público puede repartir una reserva entre varios recursos; ese
  reparto automático no está cubierto aquí porque el caso de uso de la clínica es
  por profesional.
- **Firma de documentos**: con `amma_appointment_sign` instalado, los documentos
  a firmar se envían al crearse la `calendar.event`, es decir **al cobrar**, no
  al generar el enlace.

## Pruebas mínimas

1. Cita + pedido + enlace, el paciente paga el total → aparece la cita en el
   calendario del profesional correcto y a la hora correcta.
2. El paciente no paga → no hay cita y el pedido sigue en borrador.
3. Hueco ya ocupado por otra cita del mismo profesional → el asistente avisa
   antes de crear el pedido.
4. Tipo de cita sin pago por adelantado → el asistente bloquea con el mensaje de
   configuración.

Licencia: LGPL-3. Autor: Lógica Consultores 360.
