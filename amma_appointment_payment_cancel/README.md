# Citas – Cancelación de citas pagadas

En el flujo nativo de citas con pago, una cita pagada **nunca** se puede cancelar
desde la web. No es configuración: `appointment_account_payment` sobreescribe la
comprobación de cancelación y devuelve `'no_cancel_paid'` sin llegar a mirar
cuántas horas faltan.

Este módulo hace dos cosas:

1. Las citas pagadas se cancelan con el **mismo plazo** que las demás, el de
   `min_cancellation_hours` del tipo de cita.
2. Al cancelar una cita **cobrada**, planifica una actividad **Nota de
   reembolso** para gestionar la devolución a mano.

El reembolso no se automatiza: no se emite rectificativa ni se devuelve dinero
por código.

## Cómo funciona

`_get_prevent_cancel_status` (controlador) se sobreescribe así: si la respuesta
de `super()` es `'no_cancel_paid'` —el bloqueo por pago— se sustituye por la
comprobación de horas del controlador de `appointment`. Cualquier otro motivo de
bloqueo que devuelva otro módulo se respeta tal cual.

`calendar.event.action_cancel_meeting()` se sobreescribe para planificar la
actividad después de archivar el evento.

## Dónde cae la actividad

Se busca la `calendar.booking` cuyo `calendar_event_id` es el evento cancelado y,
a partir de ella, el documento donde está el dinero:

| Caso | Documento |
|---|---|
| Reserva facturada (`calendar.booking.account_move_id`, factura publicada) | la factura |
| Reserva cobrada por pedido (`order_line_id`) y el pedido ya tiene factura publicada | la factura |
| Reserva cobrada por pedido sin factura todavía | el pedido de venta |

Se asigna al **profesional de la cita** (`calendar.event.user_id`) con
vencimiento hoy, y no se duplica: si ya hay una actividad pendiente del mismo
tipo en ese documento, no se crea otra.

## Diferencias con el planteamiento inicial

- **La factura muchas veces no existe.** El documento decía llegar a ella por
  `calendar.booking.account_move_id`. Ese campo sólo se rellena cuando el cobro
  va por factura; con `website_appointment_sale` instalado (que lo está, y del
  que dependen otros módulos de este repo) el cobro va por `sale.order` a través
  de `calendar.booking.order_line_id`, y `account_move_id` queda vacío. Por eso
  el módulo mira los dos caminos y sólo cae en el pedido cuando aún no hay
  factura.
- **El tipo de actividad no se restringe a `account.move`.** El campo real de
  `mail.activity.type` para restringir modelo es `res_model` (Selection con el
  nombre del modelo; en versiones antiguas era `res_model_id`), pero se deja
  vacío: `mail.activity.mixin.activity_schedule()` comprueba
  `activity_type.res_model != self._name` y registra un warning
  *"Invalid activity type model"* cada vez que la actividad cae en el pedido de
  venta, que aquí es un caso normal, no un error.
- **Autoría.** El documento pedía `Rebersa Soluciones` siguiendo a
  `amma_appointment_sign`. Ese manifest ya no dice eso: todos los módulos de
  este repo se pasaron a `Lógica Consultores 360` por indicación posterior, y
  este módulo sigue esa convención.

## Configuración

El plazo es el del tipo de cita (`min_cancellation_hours`). Con el valor a 0 se
puede cancelar hasta el último momento; conviene ponerle las horas que quiera la
clínica antes de instalar, porque hasta ahora ese campo no tenía ningún efecto
en las citas de pago.

## Pruebas mínimas

1. Cita pagada, con horas de sobra → el botón de cancelar en la página de la
   cita funciona y el evento se archiva.
2. Cita pagada dentro del plazo mínimo → sigue bloqueada, con el aviso de
   *no queda tiempo*.
3. Tras cancelar una cita cobrada → actividad *Nota de reembolso* en la factura
   (o en el pedido si no hay factura), asignada al profesional.
4. Cancelar dos veces / cancelar una cita sin cobro → no se duplica ni se crea
   ninguna actividad.

Licencia: LGPL-3. Autor: Lógica Consultores 360.
