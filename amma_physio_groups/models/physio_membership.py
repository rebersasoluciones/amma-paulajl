# -*- coding: utf-8 -*-
import logging
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models, Command
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


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

    auto_invoice = fields.Boolean(
        string="Facturación automática", default=True,
        help="Genera automáticamente la factura mensual y envía el correo de cobro.")
    recurring_next_date = fields.Date(
        string="Próxima factura", tracking=True,
        help="Fecha en la que se generará la siguiente factura mensual.")
    last_invoice_date = fields.Date(string="Última factura", readonly=True)

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
            if membership.state == 'active':
                continue
            vals = {'state': 'active'}
            if not membership.recurring_next_date:
                vals['recurring_next_date'] = membership.date_start or \
                    fields.Date.context_today(membership)
            if not membership.date_start:
                vals['date_start'] = fields.Date.context_today(membership)
            membership.write(vals)
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

    def action_cancel(self):
        self.write({
            'state': 'cancelled',
            'date_end': fields.Date.context_today(self),
        })
        # Cancela reservas futuras del paciente en su grupo
        for membership in self:
            future = membership.booking_ids.filtered(
                lambda b: b.state == 'booked'
                and b.session_start and b.session_start >= fields.Datetime.now())
            future.write({'state': 'cancelled'})

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
    # Facturación
    # ------------------------------------------------------------------
    def _prepare_invoice_vals(self):
        self.ensure_one()
        if not self.product_id:
            raise UserError(_(
                "Configura un producto de cuota en la suscripción %s antes de "
                "facturar.") % self.name)
        product = self.product_id
        line_name = _("Cuota %(group)s - %(month)s") % {
            'group': self.group_id.name,
            'month': fields.Date.context_today(self).strftime('%m/%Y'),
        }
        return {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.context_today(self),
            'currency_id': self.currency_id.id,
            'company_id': self.company_id.id,
            'physio_membership_id': self.id,
            'invoice_origin': self.name,
            'invoice_line_ids': [Command.create({
                'product_id': product.id,
                'name': line_name,
                'quantity': 1.0,
                'price_unit': self.price or product.lst_price,
            })],
        }

    def _create_invoice(self, auto_post=True, send_email=True):
        """Crea (y opcionalmente contabiliza y envía) la factura mensual."""
        moves = self.env['account.move']
        template = self.env.ref(
            'amma_physio_groups.mail_template_physio_invoice',
            raise_if_not_found=False)
        for membership in self:
            move = self.env['account.move'].create(
                membership._prepare_invoice_vals())
            if auto_post:
                move.action_post()
                if send_email and template and membership.partner_id.email:
                    template.send_mail(
                        move.id, force_send=False,
                        email_layout_xmlid='mail.mail_notification_light')
            membership.last_invoice_date = fields.Date.context_today(membership)
            moves |= move
        return moves

    def action_create_invoice_now(self):
        """Botón: genera la factura del mes al momento."""
        moves = self._create_invoice(auto_post=True, send_email=True)
        for membership in self.filtered(lambda m: m.recurring_next_date):
            if membership.recurring_next_date <= fields.Date.context_today(membership):
                membership.recurring_next_date += relativedelta(months=1)
        if len(moves) == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'res_id': moves.id,
                'view_mode': 'form',
            }
        return self.action_view_invoices()

    @api.model
    def _cron_generate_invoices(self, limit=200):
        """Cron diario: factura las suscripciones activas vencidas."""
        today = fields.Date.context_today(self)
        memberships = self.search([
            ('state', '=', 'active'),
            ('auto_invoice', '=', True),
            ('recurring_next_date', '!=', False),
            ('recurring_next_date', '<=', today),
        ], limit=limit)
        for membership in memberships:
            try:
                membership._create_invoice(auto_post=True, send_email=True)
                membership.recurring_next_date += relativedelta(months=1)
                self.env.cr.commit()
            except Exception as error:  # noqa: BLE001
                _logger.exception(
                    "Error facturando la suscripción %s: %s",
                    membership.name, error)
                self.env.cr.rollback()
        return True

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
