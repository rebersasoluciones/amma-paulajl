# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PhysioSessionGenerate(models.TransientModel):
    _name = 'physio.session.generate'
    _description = "Generar clases de un grupo"

    group_id = fields.Many2one(
        'physio.group', string="Grupo", required=True)
    date_from = fields.Date(
        string="Desde", required=True, default=fields.Date.context_today)
    date_to = fields.Date(string="Hasta", required=True)

    @api.onchange('date_from')
    def _onchange_date_from(self):
        if self.date_from and not self.date_to:
            self.date_to = self.date_from + relativedelta(months=1, days=-1)

    def action_generate(self):
        self.ensure_one()
        if self.date_to < self.date_from:
            raise UserError(_("La fecha 'Hasta' debe ser posterior a 'Desde'."))
        if not self.group_id.schedule_line_ids:
            raise UserError(_(
                "El grupo %s no tiene definido un horario semanal.")
                % self.group_id.name)
        sessions = self.group_id.generate_sessions(self.date_from, self.date_to)
        return {
            'type': 'ir.actions.act_window',
            'name': _("Clases generadas (%s)") % len(sessions),
            'res_model': 'physio.session',
            'view_mode': 'calendar,list,form',
            'domain': [('group_id', '=', self.group_id.id)],
            'context': {'default_group_id': self.group_id.id},
        }
