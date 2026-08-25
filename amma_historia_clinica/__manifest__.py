# -*- coding: utf-8 -*-
{
    'name': "Clínica - Historia clínica del paciente",
    'summary': "Ficha clínica en el contacto, historial de citas del paciente y "
               "registro de cada sesión con plantillas por tipo de cita.",
    'description': """
Historia clínica
================

Añade al contacto todo lo que el fisio necesita ver al abrir un paciente:

* **Ficha del paciente**: motivo de consulta, fecha de nacimiento y edad, sexo,
  profesional responsable y un aviso destacado (alergias, patologías) que se ve
  nada más abrir la ficha.
* **Historial de reservas**: todas las citas del paciente, de la más reciente a
  la más antigua, con su estado; desde cada línea se abre el registro de esa
  sesión.
* **Registro de sesión**: una anotación por visita, con plantilla. La plantilla
  se propone según el tipo de cita, así que cada tipo de cita puede tener su
  propio guion de tratamiento.

Todo queda restringido al grupo *Personal clínico*: quien no lo tenga no ve la
pestaña ni los registros.
""",
    'author': "Lógica Consultores 360",
    'website': "https://www.logicaconsultores.com",
    'category': 'Services/Appointment',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'application': True,
    'sequence': -112,
    'depends': [
        'appointment',
    ],
    'data': [
        'security/clinical_security.xml',
        'security/ir.model.access.csv',
        'data/amma_patient_type_data.xml',
        'data/amma_clinical_note_type_data.xml',
        'views/clinical_note_views.xml',
        'views/patient_type_views.xml',
        'views/res_partner_views.xml',
        'views/calendar_event_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
}
