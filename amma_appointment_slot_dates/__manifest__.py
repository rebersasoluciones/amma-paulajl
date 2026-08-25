# -*- coding: utf-8 -*-
{
    'name': "Citas - Vigencia por fechas en disponibilidad recurrente",
    'summary': "Cada franja del horario semanal puede tener fechas de vigencia, "
               "para cambiar los horarios por periodos sin acortar la ventana de reserva.",
    'description': """
Vigencia por fechas en las franjas de disponibilidad
====================================================

El horario semanal de un tipo de cita es fijo: un lunes tiene siempre las mismas
franjas. Si hace falta que un mismo día de la semana tenga horarios distintos
según el periodo (temporada, semanas alternas, una baja), hoy sólo cabe limitar
por fechas el tipo de cita entero, lo que obliga a duplicarlo.

Este módulo añade a cada franja recurrente un rango de fechas **opcional**:

* con fechas, la franja sólo genera huecos dentro de ese rango;
* sin fechas, la franja aplica siempre, exactamente como hasta ahora.

Así se pueden dejar configurados varios periodos a la vez y mantener una ventana
de reserva larga (p. ej. 90 días).
""",
    'author': "Lógica Consultores 360",
    'website': "https://www.logicaconsultores.com",
    'category': 'Services/Appointment',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': [
        'appointment',
    ],
    'data': [
        'views/appointment_type_views.xml',
    ],
    'application': True,
    'sequence': -111,
    'installable': True,
}
