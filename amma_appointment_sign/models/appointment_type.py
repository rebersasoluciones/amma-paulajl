# -*- coding: utf-8 -*-
from odoo import fields, models


class AppointmentType(models.Model):
    _inherit = 'appointment.type'

    sign_template_ids = fields.Many2many(
        'sign.template', string="Documentos a firmar",
        help="Documentos (plantillas de Firma) que el paciente debe firmar para "
             "este tipo de cita. Al confirmarse la cita se le envían por correo.")
    sign_auto_send = fields.Boolean(
        string="Enviar documentos al confirmar", default=True,
        help="Si está activo, al confirmarse una cita de este tipo se envía "
             "automáticamente el correo con los documentos a firmar.")
