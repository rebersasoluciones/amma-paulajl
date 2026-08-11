# -*- coding: utf-8 -*-
{
    'name': "Citas - Documentos y Firma en consulta",
    'summary': "Asocia documentos a firmar a cada tipo de cita, los envía al "
               "confirmar (PDF + firma online), permite firmar por QR en tablet "
               "e imprimir el PDF en blanco y el firmado.",
    'description': """
Documentos y firma para el flujo de citas
=========================================

Módulo independiente para clínicas que usan **Citas** y **Firma**:

* Asocia a cada **tipo de cita** los documentos a firmar (plantillas de Firma).
* Al **confirmarse** la cita, envía al paciente un correo (registrado en el
  chatter) con los **PDF en blanco adjuntos** y un **botón para firmar online**.
* Desde la cita puedes **solicitar firma** y mostrar un **código QR** para que el
  paciente firme en una **tablet** (o su móvil).
* **Imprime** el PDF en blanco (para rellenar a mano) y el PDF ya **firmado**.

No tiene ninguna relación con el módulo de grupos/clases: es exclusivo del flujo
de citas presenciales.
""",
    'author': "Rebersa Soluciones",
    'website': "https://www.rebersasoluciones.com",
    'category': 'Services/Appointment',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'calendar',
        'appointment',
        'sign',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_template_data.xml',
        'views/appointment_type_views.xml',
        'views/calendar_event_views.xml',
        'wizards/appointment_sign_qr_views.xml',
    ],
    'application': False,
    'installable': True,
}
