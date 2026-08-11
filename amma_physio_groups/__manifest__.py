# -*- coding: utf-8 -*-
{
    'name': "Fisioterapia - Gestión de Grupos y Clases",
    'summary': "Gestión de pacientes, grupos, clases, suscripciones mensuales, "
               "cobros con enlace de pago y portal de reservas tipo WODBUSTER.",
    'description': """
Gestión de grupos para clínica de fisioterapia
==============================================

Módulo profesional para clínicas de fisioterapia que trabajan por grupos/clases:

* **Pacientes**: alta rápida (nombre, teléfono, correo) integrada en Contactos.
* **Grupos**: cada grupo con su horario semanal, duración y capacidad; generación
  automática de las clases del mes.
* **Clases**: vista clara (calendario / kanban / lista) de qué pacientes hay en
  cada clase y cuántas plazas quedan.
* **Suscripciones**: cada paciente pertenece a un grupo mediante una suscripción
  mensual que se factura automáticamente.
* **Cobros**: al facturar se envía un correo con un botón para pagar online con los
  métodos de pago activos; panel sencillo para generar enlaces de pago al momento
  o marcar el pago en efectivo.
* **Cambios de grupo**: un paciente puede moverse de un grupo a otro.
* **Portal del paciente (estilo WODBUSTER)**: cada persona entra, ve su grupo y sus
  próximas clases, puede desapuntarse y, si está permitido y hay hueco, apuntarse a
  clases de otros grupos.
""",
    'author': "Rebersa Soluciones",
    'website': "https://www.rebersasoluciones.com",
    'category': 'Services/Wellness',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'contacts',
        'product',
        'account',
        'account_payment',
        'portal',
        'website',
        'sale_subscription',
    ],
    'data': [
        'security/physio_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/product_data.xml',
        'data/mail_template_data.xml',
        'data/subscription_data.xml',
        'data/ir_cron_data.xml',
        'wizards/physio_session_generate_views.xml',
        'wizards/physio_membership_transfer_views.xml',
        'views/physio_group_views.xml',
        'views/physio_session_views.xml',
        'views/physio_booking_views.xml',
        'views/physio_membership_views.xml',
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
        'views/sale_order_subscription_views.xml',
        'views/physio_menus.xml',
        'templates/portal_templates.xml',
    ],
    'demo': [
        'demo/physio_demo.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'amma_physio_groups/static/src/scss/portal.scss',
        ],
    },
    'application': True,
    'installable': True,
}
