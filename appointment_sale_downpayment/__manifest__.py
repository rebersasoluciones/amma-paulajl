# -*- coding: utf-8 -*-
{
    'name': "Citas - Anticipo con pedido de venta",
    'summary': "Al reservar una cita con pago, el paciente paga sólo el anticipo "
               "configurado sobre un pedido de venta; el resto se factura después "
               "desde el mismo pedido.",
    'description': """
Anticipos en las reservas de Citas
==================================

El "Pay to Book" nativo (*appointment_account_payment*) cobra el precio completo
del producto de la cita y emite una factura suelta por ese importe, sin relación
con la factura del resto del servicio.

Este módulo sustituye ese destino: al reservar se crea un **pedido de venta** con
la línea del servicio completo, con ``require_payment`` y el porcentaje de
anticipo del tipo de cita, y se lleva al paciente al portal del pedido, que ya
cobra únicamente el anticipo. En cuanto el pago alcanza ese importe, Odoo
confirma el pedido y la cita pasa al calendario del profesional.

El resto se factura desde el mismo pedido con el asistente estándar de facturas,
que descuenta automáticamente los anticipos ya facturados.
""",
    'author': "Lógica Consultores 360",
    'website': "https://www.logicaconsultores.com",
    'category': 'Services/Appointment',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': [
        'appointment_account_payment',
        'website_appointment_sale',
    ],
    'data': [
        'views/appointment_type_views.xml',
    ],
    'installable': True,
}
