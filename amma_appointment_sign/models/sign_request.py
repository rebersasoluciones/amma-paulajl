# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SignRequest(models.Model):
    _inherit = 'sign.request'

    calendar_event_id = fields.Many2one(
        'calendar.event', string="Cita", index=True, ondelete='set null',
        help="Cita a la que pertenecen estos documentos a firmar.")
    appointment_type_id = fields.Many2one(
        related='calendar_event_id.appointment_type_id', store=True,
        string="Tipo de cita")
    appointment_start = fields.Datetime(
        related='calendar_event_id.start', store=True, string="Fecha de la cita")
    signer_partner_id = fields.Many2one(
        'res.partner', string="Firmante", store=True,
        compute='_compute_signer_partner')

    @api.depends('request_item_ids.partner_id')
    def _compute_signer_partner(self):
        for request in self:
            request.signer_partner_id = request.request_item_ids[:1].partner_id
