# -*- coding: utf-8 -*-
from odoo import _, Command, fields, models
from odoo.exceptions import UserError


class PhysioEnrollWizard(models.TransientModel):
    _name = 'physio.enroll.wizard'
    _description = "Alta de suscripciones de fisioterapia"

    group_id = fields.Many2one(
        'physio.group', string="Grupo", required=True)
    partner_ids = fields.Many2many(
        'res.partner', string="Pacientes", required=True)
    date_start = fields.Date(
        string="Fecha de alta", default=fields.Date.context_today)
    auto_confirm = fields.Boolean(
        string="Confirmar (activar y apuntar a clases)", default=True,
        help="Si está activo, la suscripción se confirma: empieza la facturación "
             "recurrente y el paciente queda apuntado a las clases del grupo.")

    # Informativos (se rellenan solos desde el grupo)
    product_id = fields.Many2one(
        related='group_id.product_id', string="Producto de cuota", readonly=True)
    plan_id = fields.Many2one(
        related='group_id.subscription_plan_id', string="Plan", readonly=True)
    price = fields.Monetary(related='group_id.price', string="Cuota mensual", readonly=True)
    currency_id = fields.Many2one(related='group_id.currency_id')

    def action_create(self):
        self.ensure_one()
        group = self.group_id
        if not group.product_id or not group.subscription_plan_id:
            raise UserError(_(
                "El grupo «%s» debe tener un producto de cuota y un plan de "
                "suscripción configurados (pestaña Facturación).") % group.name)
        if not group.product_id.recurring_invoice:
            raise UserError(_(
                "El producto de cuota del grupo debe ser un producto recurrente "
                "(marca «Producto de suscripción»)."))

        Sale = self.env['sale.order']
        created = Sale
        skipped = self.env['res.partner']
        for partner in self.partner_ids:
            existing = Sale.search([
                ('physio_group_id', '=', group.id),
                ('partner_id', '=', partner.id),
                ('subscription_state', 'in', ('1_draft', '3_progress', '4_paused')),
            ], limit=1)
            if existing:
                created |= existing
                skipped |= partner
                continue
            if not partner.is_physio_patient:
                partner.is_physio_patient = True
            order = Sale.create({
                'partner_id': partner.id,
                'physio_group_id': group.id,
                'plan_id': group.subscription_plan_id.id,
                'start_date': self.date_start or fields.Date.context_today(self),
                'order_line': [Command.create({
                    'product_id': group.product_id.id,
                    'product_uom_qty': 1,
                    'price_unit': group.price or group.product_id.lst_price,
                })],
            })
            if self.auto_confirm:
                order.action_confirm()
            created |= order

        return {
            'type': 'ir.actions.act_window',
            'name': _("Suscripciones creadas"),
            'res_model': 'sale.order',
            'domain': [('id', 'in', created.ids)],
            'view_mode': 'list,form',
            'search_view_id': self.env.ref(
                'sale_subscription.sale_subscription_view_search').id,
            'views': [
                (self.env.ref('sale_subscription.sale_subscription_view_tree').id, 'list'),
                (self.env.ref('sale_subscription.sale_subscription_primary_form_view').id, 'form'),
            ],
        }
