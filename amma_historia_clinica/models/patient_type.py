# -*- coding: utf-8 -*-
from odoo import fields, models


class PatientType(models.Model):
    _name = 'amma.patient.type'
    _description = "Motivo de consulta"
    _order = 'sequence, id'

    name = fields.Char(string="Nombre", required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    color = fields.Integer(string="Color")
