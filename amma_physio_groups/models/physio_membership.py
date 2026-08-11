# -*- coding: utf-8 -*-
from odoo import _, api, fields, models, Command


class PhysioMembership(models.Model):
    _name = 'physio.membership'
    _description = "Suscripción de paciente a grupo"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string="Referencia", required=True, copy=False, readonly=True,
        default=lambda self: _("Nuevo"))
    partner_id = fields.Many2one(
        'res.partner', string="Paciente", required=True, tracking=True, index=True)
    group_id = fields.Many2one(
        'physio.group', string="Grupo", required=True, tracking=True, index=True)

    company_id = fields.Many2one(
        'res.company', string="Compañía", required=True,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')

    product_id = fields.Many2one(
        'product.product', string="Producto de cuota",
        domain="[('sale_ok', '=', True)]")
    price = fields.Monetary(
        string="Cuota mensual", currency_field='currency_id', tracking=True)

    state = fields.Selection([
        ('draft', "Borrador"),
        ('active', "Activa"),
        ('paused', "Pausada"),
        ('cancelled', "Cancelada"),
    ], string="Estado", default='draft', required=True, tracking=True, index=True)
    active = fields.Boolean(default=True)

    date_start = fields.Date(
        string="Alta", default=fields.Date.context_today, tracking=True)
    date_end = fields.Date(string="Baja", tracking=True)

    # -- Facturación recurrente --
    max_classes_per_month = fields.Integer(
        string="Tope de clases al mes",
        help="Número máximo de clases al mes para este paciente (0 = sin límite). "
             "Por defecto hereda el valor del grupo.")

    # -- Suscripción nativa (facturación recurrente) --
    subscription_id = fields.Many2one(
        'sale.order', string="Suscripción", readonly=True, copy=False,
        help="Suscripción nativa de Odoo que factura esta cuota de forma "
             "recurrente (fecha de inicio, posición fiscal, condiciones de pago...).")
    subscription_state = fields.Selection(
        related='subscription_id.subscription_state', string="Estado de la suscripción")
    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', string="Posición fiscal",
        help="Se aplica a las facturas de la suscripción.")
    payment_term_id = fields.Many2one(
        'account.payment.term', string="Condiciones de pago")
    pricelist_id = fields.Many2one(
        'product.pricelist', string="Tarifa")
    recurring_next_date = fields.Date(
        related='subscription_id.next_invoice_date', store=True,
        string="Próxima factura", readonly=True)

    invoice_ids = fields.One2many(
        'account.move', 'physio_membership_id', string="Facturas")
    invoice_count = fields.Integer(compute='_compute_invoice_stats')
    amount_due = fields.Monetary(
        string="Pendiente de pago", compute='_compute_invoice_stats',
        currency_field='currency_id')
    payment_status = fields.Selection([
        ('no_invoice', "Sin facturas"),
        ('paid', "Al día"),
        ('due', "Pendiente"),
    ], string="Estado de pago", compute='_compute_invoice_stats')

    booking_ids = fields.One2many(
        'physio.booking', 'membership_id', string="Reservas")
    note = fields.Text(string="Notas")

    # ------------------------------------------------------------------
    # Cálculos
    # ------------------------------------------------------------------
    @api.depends('invoice_ids.state', 'invoice_ids.payment_state',
                 'invoice_ids.amount_residual')
    def _compute_invoice_stats(self):
        for membership in self:
            invoices = membership.invoice_ids.filtered(
                lambda m: m.state == 'posted')
            membership.invoice_count = len(membership.invoice_ids)
            membership.amount_due = sum(invoices.mapped('amount_residual'))
            if not invoices:
                membership.payment_status = 'no_invoice'
            elif membership.amount_due > 0:
                membership.payment_status = 'due'
            else:
                membership.payment_status = 'paid'

    @api.onchange('group_id')
    def _onchange_group_id(self):
        if self.group_id:
            if not self.product_id:
                self.product_id = self.group_id.product_id
            if not self.price:
                self.price = self.group_id.price or (
                    self.group_id.product_id.lst_price
                    if self.group_id.product_id else 0.0)
            if not self.max_classes_per_month:
                self.max_classes_per_month = self.group_id.max_classes_per_month

    # ------------------------------------------------------------------
    # Creación
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _("Nuevo")) == _("Nuevo"):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'physio.membership') or _("Nuevo")
            # Valores por defecto heredados del grupo
            group = self.env['physio.group'].browse(vals.get('group_id'))
            if group:
                if not vals.get('product_id') and group.product_id:
                    vals['product_id'] = group.product_id.id
                if not vals.get('price'):
                    vals['price'] = group.price or (
                        group.product_id.lst_price if group.product_id else 0.0)
                if not vals.get('max_classes_per_month'):
                    vals['max_classes_per_month'] = group.max_classes_per_month
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Transiciones de estado
    # ------------------------------------------------------------------
    def action_activate(self):
        for membership in self:
            if membership.state != 'active':
                vals = {'state': 'active'}
                if not membership.date_start:
                    vals['date_start'] = fields.Date.context_today(membership)
                membership.write(vals)
            # Crea/reactiva la suscripción nativa de facturación
            membership._ensure_subscription()
        # Reserva su plaza en las clases futuras de su grupo
        self._autoenroll_future_sessions()

    def _autoenroll_future_sessions(self):
        """Apunta al paciente en todas las clases futuras de su grupo (plaza
        asignada), respetando capacidad y sin duplicar."""
        Booking = self.env['physio.booking']
        for membership in self.filtered(
                lambda m: m.state == 'active' and m.group_id.auto_enroll):
            sessions = self.env['physio.session'].search([
                ('group_id', '=', membership.group_id.id),
                ('state', '=', 'scheduled'),
                ('start_datetime', '>=', fields.Datetime.now()),
            ])
            for session in sessions:
                already = session.booking_ids.filtered(
                    lambda b: b.partner_id == membership.partner_id
                    and b.state in ('booked', 'attended'))
                if already or session.seats_available <= 0:
                    continue
                Booking.create({
                    'session_id': session.id,
                    'partner_id': membership.partner_id.id,
                    'membership_id': membership.id,
                    'is_cross_booking': False,
                    'state': 'booked',
                })

    def action_pause(self):
        self.write({'state': 'paused'})
        for membership in self.filtered('subscription_id'):
            if membership.subscription_id.subscription_state == '3_progress':
                membership.subscription_id.sudo().pause_subscription()

    def action_cancel(self):
        self.write({
            'state': 'cancelled',
            'date_end': fields.Date.context_today(self),
        })
        for membership in self:
            # Cancela reservas futuras del paciente en su grupo
            future = membership.booking_ids.filtered(
                lambda b: b.state == 'booked'
                and b.session_start and b.session_start >= fields.Datetime.now())
            future.write({'state': 'cancelled'})
            # Cierra la suscripción nativa
            if membership.subscription_id and membership.subscription_id.subscription_state in (
                    '3_progress', '4_paused'):
                membership.subscription_id.sudo().set_close()

    def action_draft(self):
        self.write({'state': 'draft'})

    # ------------------------------------------------------------------
    # Cambio de grupo (mantiene la suscripción)
    # ------------------------------------------------------------------
    def action_open_transfer(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Cambiar de grupo"),
            'res_model': 'physio.membership.transfer',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_membership_id': self.id},
        }

    # ------------------------------------------------------------------
    # Suscripción nativa (facturación recurrente)
    # ------------------------------------------------------------------
    def _prepare_subscription_vals(self):
        self.ensure_one()
        product = self.product_id or self.group_id.product_id
        vals = {
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
            'plan_id': self.group_id.subscription_plan_id.id,
            'physio_membership_id': self.id,
            'physio_group_id': self.group_id.id,
            'start_date': self.date_start or fields.Date.context_today(self),
            'client_order_ref': self.name,
            'order_line': [Command.create({
                'product_id': product.id,
                'product_uom_qty': 1,
                'price_unit': self.price or product.lst_price,
            })],
        }
        if self.fiscal_position_id:
            vals['fiscal_position_id'] = self.fiscal_position_id.id
        if self.payment_term_id:
            vals['payment_term_id'] = self.payment_term_id.id
        if self.pricelist_id:
            vals['pricelist_id'] = self.pricelist_id.id
        return vals

    def _ensure_subscription(self):
        """Crea y confirma la suscripción nativa si no existe; si ya existe,
        la reactiva cuando estaba pausada o cerrada."""
        for membership in self:
            sub = membership.subscription_id
            if sub:
                if sub.subscription_state == '4_paused':
                    sub.sudo().resume_subscription()
                elif sub.subscription_state in ('5_renewed', '6_churn'):
                    sub.sudo().reopen_order()
                continue
            group = membership.group_id
            product = membership.product_id or group.product_id
            if not group.subscription_plan_id or not product or not product.recurring_invoice:
                membership.message_post(body=_(
                    "No se ha creado la suscripción de facturación: revisa que el "
                    "grupo tenga un <b>plan de suscripción</b> y un <b>producto "
                    "recurrente</b>."))
                continue
            sub = self.env['sale.order'].sudo().create(
                membership._prepare_subscription_vals())
            sub.action_confirm()
            membership.subscription_id = sub.id
            membership.message_post(body=_(
                "Suscripción de facturación creada: %s") % sub.name)

    def action_view_subscription(self):
        self.ensure_one()
        if not self.subscription_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _("Suscripción"),
            'res_model': 'sale.order',
            'res_id': self.subscription_id.id,
            'view_mode': 'form',
        }

    def action_view_invoices(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Facturas de %s") % self.name,
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('physio_membership_id', '=', self.id)],
            'context': {'default_move_type': 'out_invoice'},
        }
