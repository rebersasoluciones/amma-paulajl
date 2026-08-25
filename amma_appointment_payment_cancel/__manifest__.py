# -*- coding: utf-8 -*-
{
    'name': "Citas - Cancelación de citas pagadas",
    'summary': "Permite cancelar las citas pagadas dentro del plazo de horas del "
               "tipo de cita y planifica una actividad para gestionar el reembolso.",
    'description': """
Cancelación de citas pagadas
============================

En el flujo nativo de citas con pago (*appointment_account_payment*), una cita
pagada **nunca** se puede cancelar desde la web: el módulo bloquea la
cancelación sin llegar a mirar cuántas horas faltan.

Este módulo:

* aplica a las citas pagadas el mismo plazo que a las demás
  (*Cancelar con antelación mínima de*, ``min_cancellation_hours``), y
* al cancelar una cita que está cobrada, planifica una actividad **Nota de
  reembolso** en la factura (o, si el cobro fue por pedido de venta sin factura
  todavía, en el pedido) asignada al profesional de la cita.

El reembolso no se automatiza: no se emite ninguna rectificativa ni se devuelve
dinero por código. La actividad es el aviso para gestionarlo a mano.
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
        'data/mail_activity_type_data.xml',
    ],
    'installable': True,
}
