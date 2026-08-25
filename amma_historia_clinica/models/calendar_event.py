# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    clinical_note_ids = fields.One2many(
        'amma.clinical.note', 'calendar_event_id', string="Registros de sesión")
    clinical_note_count = fields.Integer(compute='_compute_clinical_note_count')

    @api.depends('clinical_note_ids')
    def _compute_clinical_note_count(self):
        for event in self:
            event.clinical_note_count = len(event.clinical_note_ids)

    def _get_clinical_patient(self):
        """ Asistente de la cita que no es personal de la clínica. """
        self.ensure_one()
        staff_partners = self.appointment_type_id.staff_user_ids.partner_id | self.user_id.partner_id
        return (self.partner_ids - staff_partners)[:1] or self.appointment_booker_id

    def _get_clinical_note_type(self):
        self.ensure_one()
        if not self.appointment_type_id:
            return self.env['amma.clinical.note.type']
        return self.env['amma.clinical.note.type'].search(
            [('appointment_type_ids', 'in', self.appointment_type_id.ids)], limit=1)

    def action_open_clinical_note(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'name': _("Registro de sesión"),
            'res_model': 'amma.clinical.note',
            'view_mode': 'form',
            'target': 'new',
        }
        note = self.clinical_note_ids[:1]
        if note:
            action['res_id'] = note.id
            return action
        action['context'] = {
            'default_calendar_event_id': self.id,
            'default_partner_id': self._get_clinical_patient().id,
            'default_date': fields.Datetime.to_string(self.start),
            'default_user_id': self.user_id.id,
            'default_note_type_id': self._get_clinical_note_type().id,
        }
        return action
