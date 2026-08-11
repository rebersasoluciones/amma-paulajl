# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    physio_membership_id = fields.Many2one(
        'physio.membership', string="Suscripción de fisioterapia",
        ondelete='set null', index=True, copy=False)
    physio_group_id = fields.Many2one(
        'physio.group', string="Grupo de fisioterapia", copy=False)

    def _prepare_invoice(self):
        """Propaga el enlace de fisioterapia a las facturas generadas por la
        suscripción nativa (para los cobros y el correo de pago)."""
        vals = super()._prepare_invoice()
        if self.physio_membership_id:
            vals['physio_membership_id'] = self.physio_membership_id.id
        return vals
