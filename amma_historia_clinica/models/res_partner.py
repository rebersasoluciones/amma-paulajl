# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_patient = fields.Boolean(string="Es paciente")
    patient_birthdate = fields.Date(string="Fecha de nacimiento")
    patient_age = fields.Integer(string="Edad", compute='_compute_patient_age')
    patient_gender = fields.Selection(
        [('female', "Mujer"), ('male', "Hombre"), ('other', "Otro")], string="Sexo")
    patient_type_id = fields.Many2one('amma.patient.type', string="Motivo de consulta")
    patient_responsible_id = fields.Many2one(
        'res.users', string="Profesional responsable", domain="[('share', '=', False)]")
    patient_alert = fields.Text(
        string="Alertas importantes",
        help="Se muestra destacado al abrir la ficha: alergias, patologías, avisos.")

    patient_appointment_ids = fields.Many2many(
        'calendar.event', string="Historial de reservas",
        compute='_compute_patient_appointments')
    patient_visit_count = fields.Integer(
        string="Visitas", compute='_compute_patient_appointments')
    patient_first_visit = fields.Datetime(
        string="Primera visita", compute='_compute_patient_appointments')
    patient_last_visit = fields.Datetime(
        string="Última visita", compute='_compute_patient_appointments')

    clinical_note_ids = fields.One2many(
        'amma.clinical.note', 'partner_id', string="Registros de sesión")
    clinical_note_count = fields.Integer(compute='_compute_clinical_note_count')

    @api.depends('patient_birthdate')
    def _compute_patient_age(self):
        today = fields.Date.context_today(self)
        for partner in self:
            birthdate = partner.patient_birthdate
            partner.patient_age = birthdate and (
                today.year - birthdate.year
                - ((today.month, today.day) < (birthdate.month, birthdate.day))) or 0

    def _compute_patient_appointments(self):
        now = fields.Datetime.now()
        events_model = self.env['calendar.event'].with_context(active_test=False)
        for partner in self:
            events = events_model.search(
                partner._get_patient_appointment_domain(), order='start desc')
            visits = events.filtered(
                lambda event: event.start <= now
                and event.appointment_status not in ('cancelled', 'no_show'))
            partner.patient_appointment_ids = events
            partner.patient_visit_count = len(visits)
            partner.patient_first_visit = visits[-1].start if visits else False
            partner.patient_last_visit = visits[0].start if visits else False

    @api.depends('clinical_note_ids')
    def _compute_clinical_note_count(self):
        notes_data = self.env['amma.clinical.note']._read_group(
            [('partner_id', 'in', self.ids)], ['partner_id'], ['__count'])
        mapped_data = {partner.id: count for partner, count in notes_data}
        for partner in self:
            partner.clinical_note_count = mapped_data.get(partner.id, 0)

    def _get_patient_appointment_domain(self):
        self.ensure_one()
        return [('partner_ids', 'in', self.ids), ('appointment_type_id', '!=', False)]

    def action_open_patient_appointments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Historial de reservas"),
            'res_model': 'calendar.event',
            'view_mode': 'list,form',
            'domain': self._get_patient_appointment_domain(),
            'context': {'active_test': False, 'create': False},
        }

    def action_open_clinical_notes(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Registros de sesión"),
            'res_model': 'amma.clinical.note',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }
