# Citas – Anticipo con pedido de venta

Sustituye el destino del "Pay to Book" nativo: al reservar una cita con pago, en
lugar de emitir una factura suelta por el precio del producto de reserva, se crea
un **pedido de venta** con el servicio completo y se cobra sólo el **anticipo**
configurado en el tipo de cita.

## Flujo

1. El paciente rellena el formulario público de la cita. `appointment_account_payment`
   crea la reserva (`calendar.booking`) y llama a `_redirect_to_payment()`.
2. Este módulo sobrescribe ese método: crea un `sale.order` con
   `require_payment=True`, `require_signature=False` y
   `prepayment_percent = tipo de cita.downpayment_prepayment_percent`, con una
   línea del producto del servicio enlazada a la reserva (`calendar_booking_ids`),
   y redirige a `order.get_portal_url()` → `/my/orders/<id>?access_token=…`.
3. El portal de pedidos ya muestra y cobra únicamente el anticipo
   (`sale.order._get_prepayment_required_amount()`), sin tocar plantillas.
4. Al llegar el pago, `payment.transaction._check_amount_and_confirm_order()`
   confirma el pedido **en cuanto se alcanza el anticipo** (no hace falta el 100%).
5. La confirmación dispara `sale.order._action_confirm()` de
   `website_appointment_sale` → `calendar_booking_ids._make_event_from_paid_booking()`
   → la cita entra en el calendario del profesional.
6. El resto se factura desde el mismo pedido con el asistente estándar
   (`sale.advance.payment.inv`, opción de factura normal), que descuenta los
   anticipos ya facturados.

Todo lo que no es el paso 2 es mecanismo nativo; este módulo no lo reimplementa.

## Configuración necesaria

1. **Cuenta de anticipos**: Ajustes → Facturación → *Downpayment Account*
   (`res.company.downpayment_account_id`). Si está vacía, el anticipo va a la
   cuenta de ingresos del producto en vez de a anticipos de cliente.
2. **Factura de anticipo automática**: parámetro de sistema `sale.automatic_invoice`.
   Activo → la factura de anticipo se genera y postea sola al cobrar. Inactivo →
   se genera a mano desde el pedido.
3. **Producto de cada tipo de cita**: pasa a representar el **precio completo del
   servicio**, no una señal fija. Revisar los tipos ya configurados con
   *Pago por adelantado* antes de activar el flujo, porque hoy apuntan al producto
   de señal.
4. **Anticipo por tipo de cita**: campo *Anticipo* junto al precio, en el
   formulario del tipo de cita. Por defecto toma el porcentaje de la compañía
   (`res.company.prepayment_percent`, 100% de fábrica).
5. Debe haber un **proveedor de pago publicado** para que el portal cobre.

## Discrepancias con la especificación (verificadas en el código)

- **Dependencia de `website_appointment_sale`.** La especificación pedía depender
  sólo de `appointment_account_payment` + `sale` y replicar en este módulo
  `calendar.booking.order_line_id`, `sale.order.line.calendar_booking_ids` /
  `calendar_event_id` y el override de `_action_confirm()`. En esta instancia
  `website_appointment_sale` **ya está instalado** (se auto-instala con
  `appointment_account_payment` + `website_sale`), así que:
  - esos campos y ese override ya existen; redefinirlos sería duplicarlos;
  - y, sobre todo, `website_appointment_sale` **también sobrescribe
    `_redirect_to_payment()`**. Los controladores de Odoo se combinan con
    `type(name, tuple(reversed(leaf_controllers)), {})` (`odoo/http.py`), de modo
    que gana el módulo cargado más tarde. Sin depender de él, su versión (carrito
    de la tienda, 100% del importe) ganaría y este módulo quedaría muerto.

  Si algún día se desinstala `website_appointment_sale`, hay que replicar aquí
  los tres campos y el override de `_action_confirm()` y quitar la dependencia.
- **Compañía del pedido**: `appointment.type` no tiene `company_id` en 19.0, así
  que el pedido toma la compañía del entorno de la petición (la del sitio web).
- `get_portal_url()` ya llama a `_portal_ensure_token()`, no hace falta invocarlo
  aparte.
- No se fuerza `action_quotation_sent()`: `_has_to_be_paid()` acepta `draft` y
  `_post_process()` ya pasa el pedido a *enviado* cuando llega el pago.

## Decisiones tomadas por defecto (preguntas abiertas del cliente)

- **Un pedido por reserva.** Es lo que hace hoy el flujo de facturas. Si se quiere
  agrupar varias reservas de la misma sesión en un pedido, el punto a cambiar es
  `_prepare_downpayment_order()` (buscar un pedido en borrador del paciente antes
  de crear uno).
- **Anticipo por tipo de cita**, no global, para permitir 100% en primera visita y
  parcial en el resto.
- **Factura final manual** desde el pedido. La automatización por cron cuando pasa
  la fecha de la cita queda para una segunda fase.

## Pendiente de probar en la instancia

Sin entorno Odoo en el momento de escribirlo: sólo validación de sintaxis. Falta
comprobar reserva → portal con importe reducido → pago del anticipo → cita en el
calendario → factura de anticipo con la cuenta correcta → factura final
descontando el anticipo.

Licencia: LGPL-3. Autor: Lógica Consultores 360.
