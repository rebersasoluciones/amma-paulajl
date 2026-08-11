# -*- coding: utf-8 -*-
from odoo import _, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    physio_membership_id = fields.Many2one(
        'physio.membership', string="Suscripción de fisioterapia",
        ondelete='set null', index=True, copy=False)
    physio_group_id = fields.Many2one(
        related='physio_membership_id.group_id', store=True,
        string="Grupo de fisioterapia")

    def action_physio_payment_link(self):
        """Abre el asistente para generar un enlace de pago de la factura."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Generar enlace de pago"),
            'res_model': 'payment.link.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_model': 'account.move',
                'active_id': self.id,
            },
        }

    def action_physio_send_invoice_email(self):
        """Reenvía el correo de cobro con el botón de pago."""
        self.ensure_one()
        template = self.env.ref(
            'amma_physio_groups.mail_template_physio_invoice',
            raise_if_not_found=False)
        if template and self.partner_id.email:
            template.send_mail(
                self.id, force_send=True,
                email_layout_xmlid='mail.mail_notification_light')
        return True
