# -*- coding: utf-8 -*-
{
    'name': "Citas - Reserva manual con enlace de pago",
    'summary': "Crea desde el backend una cita con pago por adelantado: genera el "
               "pedido de venta y el enlace de pago, y la cita se confirma al cobrar.",
    'description': """
Reserva manual de cita con pago
===============================

El flujo nativo de citas con pago por adelantado (*appointment_account_payment* +
*website_appointment_sale*) sólo se puede iniciar desde el formulario público de
la web. Este módulo añade el punto de entrada que falta: un asistente de backend
para que el personal de la clínica reserve la cita en nombre del paciente.

Al confirmar el asistente:

* se crea la reserva (``calendar.booking``) con sus líneas de capacidad,
* se comprueba la disponibilidad real del hueco antes de vender nada,
* se crea (o se reutiliza) un **pedido de venta** en borrador con la línea de la
  cita, y
* se abre el asistente nativo de **enlace de pago** para enviárselo al paciente.

La cita (``calendar.event``) no aparece en el calendario del profesional hasta
que el pedido se confirma: automáticamente al cobrar, o a mano desde el pedido.

No se emite ninguna factura antes del cobro, para no generar apuntes en
SII/Verifactu de una cita que puede no llegar a pagarse.
""",
    'author': "Lógica Consultores 360",
    'website': "https://www.logicaconsultores.com",
    'category': 'Services/Appointment',
    'version': '19.0.1.0.1',
    'license': 'LGPL-3',
    'application': True,
    'sequence': -111,
    'depends': [
        'website_appointment_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/appointment_manual_booking_views.xml',
    ],
    'installable': True,
}
