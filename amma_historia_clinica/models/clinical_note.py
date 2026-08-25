# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.tools.misc import format_datetime


class ClinicalNoteType(models.Model):
    _name = 'amma.clinical.note.type'
    _description = "Plantilla de registro clínico"
    _order = 'sequence, id'

    name = fields.Char(string="Nombre", required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    appointment_type_ids = fields.Many2many(
        'appointment.type', string="Tipos de cita",
        help="Tipos de cita para los que se propone esta plantilla al registrar la sesión.")
    template_body = fields.Html(string="Plantilla")


class ClinicalNote(models.Model):
    _name = 'amma.clinical.note'
    _description = "Registro de sesión"
    _order = 'date desc, id desc'
    _rec_name = 'partner_id'

    partner_id = fields.Many2one(
        'res.partner', string="Paciente", required=True, index=True, ondelete='cascade')
    calendar_event_id = fields.Many2one(
        'calendar.event', string="Cita", index='btree_not_null', ondelete='set null')
    appointment_type_id = fields.Many2one(
        related='calendar_event_id.appointment_type_id', string="Tipo de cita", store=True)
    date = fields.Datetime(
        string="Fecha", required=True, default=fields.Datetime.now, index=True)
    user_id = fields.Many2one(
        'res.users', string="Profesional", default=lambda self: self.env.user,
        domain="[('share', '=', False)]")
    note_type_id = fields.Many2one('amma.clinical.note.type', string="Plantilla")
    body = fields.Html(string="Registro")
    attachment_ids = fields.Many2many(
        'ir.attachment', 'amma_clinical_note_attachment_rel', 'note_id', 'attachment_id',
        string="Ficheros")

    @api.depends('partner_id', 'note_type_id', 'date')
    def _compute_display_name(self):
        for note in self:
            label = note.note_type_id.name or _("Registro")
            if note.date:
                label = "%s · %s" % (label, format_datetime(note.env, note.date))
            note.display_name = label

    @api.onchange('note_type_id')
    def _onchange_note_type_id(self):
        if self.note_type_id and not self.body:
            self.body = self.note_type_id.template_body
