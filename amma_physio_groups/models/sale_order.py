# -*- coding: utf-8 -*-
from odoo import Command, api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    physio_membership_id = fields.Many2one(
        'physio.membership', string="Inscripción de fisioterapia",
        ondelete='set null', index=True, copy=False)
    physio_group_id = fields.Many2one(
        'physio.group', string="Grupo de fisioterapia", copy=False, index=True)
    physio_amount_due = fields.Monetary(
        string="Pendiente de pago", compute='_compute_physio_payment_status',
        currency_field='currency_id')
    physio_payment_status = fields.Selection([
        ('no_invoice', "Sin facturas"),
        ('paid', "Al corriente"),
        ('due', "Pendiente"),
    ], string="Estado de pago", compute='_compute_physio_payment_status',
        help="Al corriente si no hay importe pendiente en sus facturas; "
             "Pendiente si tiene facturas sin cobrar.")

    @api.depends('physio_group_id', 'invoice_ids.state',
                 'invoice_ids.payment_state', 'invoice_ids.amount_residual')
    def _compute_physio_payment_status(self):
        for order in self:
            invoices = order.invoice_ids.filtered(
                lambda m: m.move_type == 'out_invoice' and m.state == 'posted')
            due = sum(invoices.mapped('amount_residual'))
            order.physio_amount_due = due
            if not order.physio_group_id:
                order.physio_payment_status = False
            elif not invoices:
                order.physio_payment_status = 'no_invoice'
            elif order.currency_id.compare_amounts(due, 0) > 0:
                order.physio_payment_status = 'due'
            else:
                order.physio_payment_status = 'paid'

    # Mapa estado de suscripción nativa -> estado de la inscripción de fisioterapia
    _PHYSIO_STATE_MAP = {
        '1_draft': 'draft',
        '2_renewal': 'draft',
        '3_progress': 'active',
        '4_paused': 'paused',
        '5_renewed': 'cancelled',
        '6_churn': 'cancelled',
        '7_upsell': 'draft',
    }

    @api.onchange('physio_group_id')
    def _onchange_physio_group_id(self):
        """Al elegir el grupo, propone el plan y el producto de cuota."""
        group = self.physio_group_id
        if not group:
            return
        if group.subscription_plan_id and not self.plan_id:
            self.plan_id = group.subscription_plan_id
        if group.product_id and not self.order_line:
            self.order_line = [Command.create({
                'product_id': group.product_id.id,
                'product_uom_qty': 1,
                'price_unit': group.price or group.product_id.lst_price,
            })]

    def _prepare_invoice(self):
        """Propaga el enlace de fisioterapia a las facturas de la suscripción."""
        vals = super()._prepare_invoice()
        if self.physio_membership_id:
            vals['physio_membership_id'] = self.physio_membership_id.id
        return vals

    # ------------------------------------------------------------------
    # Sincronización con la inscripción de fisioterapia (clases/portal)
    # ------------------------------------------------------------------
    def _physio_sync_membership(self):
        Membership = self.env['physio.membership'].sudo()
        for order in self:
            if not order.physio_group_id:
                continue
            target = self._PHYSIO_STATE_MAP.get(order.subscription_state, 'draft')
            membership = order.physio_membership_id or Membership.search(
                [('subscription_id', '=', order.id)], limit=1)
            if not membership:
                membership = Membership.create({
                    'partner_id': order.partner_id.id,
                    'group_id': order.physio_group_id.id,
                    'company_id': order.company_id.id,
                    'subscription_id': order.id,
                    'date_start': order.start_date or fields.Date.context_today(order),
                    'state': target,
                })
                order.physio_membership_id = membership.id
            else:
                update = {}
                if membership.state != target:
                    update['state'] = target
                group_changed = membership.group_id.id != order.physio_group_id.id
                if group_changed:
                    update['group_id'] = order.physio_group_id.id
                if update:
                    membership.write(update)
                if group_changed:
                    # Libera las plazas del grupo anterior antes de reasignar
                    membership._cancel_future_bookings()
            # Efectos: apuntar o liberar plazas según el estado
            if target == 'active':
                membership._autoenroll_future_sessions()
            elif target == 'cancelled':
                membership._cancel_future_bookings()

    def write(self, vals):
        res = super().write(vals)
        if 'physio_group_id' in vals:
            self.filtered(lambda o: o.physio_membership_id)._physio_sync_membership()
        return res

    def action_confirm(self):
        res = super().action_confirm()
        self._physio_sync_membership()
        return res

    def pause_subscription(self):
        res = super().pause_subscription()
        self._physio_sync_membership()
        return res

    def resume_subscription(self):
        res = super().resume_subscription()
        self._physio_sync_membership()
        return res

    def set_close(self, close_reason_id=None, renew=False):
        res = super().set_close(close_reason_id=close_reason_id, renew=renew)
        self._physio_sync_membership()
        return res
