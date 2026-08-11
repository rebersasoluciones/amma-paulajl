# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_physio_patient = fields.Boolean(
        string="Es paciente", help="Marca este contacto como paciente de la clínica.")
    physio_membership_ids = fields.One2many(
        'physio.membership', 'partner_id', string="Suscripciones de fisioterapia")
    physio_membership_count = fields.Integer(compute='_compute_physio_counts')
    physio_active_group_ids = fields.Many2many(
        'physio.group', string="Grupos activos",
        compute='_compute_physio_counts')

    @api.depends('physio_membership_ids.state')
    def _compute_physio_counts(self):
        for partner in self:
            memberships = partner.physio_membership_ids
            partner.physio_membership_count = len(memberships)
            partner.physio_active_group_ids = memberships.filtered(
                lambda m: m.state == 'active').mapped('group_id')

    def action_open_physio_enroll(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Crear suscripción de fisioterapia"),
            'res_model': 'physio.enroll.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_ids': [(6, 0, [self.id])],
                'default_is_physio_patient': True,
            },
        }

    def action_view_physio_memberships(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Suscripciones"),
            'res_model': 'physio.membership',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {
                'default_partner_id': self.id,
                'default_is_physio_patient': True,
            },
        }
