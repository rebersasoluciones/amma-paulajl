# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, time

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PhysioGroup(models.Model):
    _name = 'physio.group'
    _description = "Grupo de fisioterapia"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    name = fields.Char(string="Nombre del grupo", required=True, tracking=True)
    code = fields.Char(string="Código", copy=False)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    color = fields.Integer(string="Color")
    description = fields.Text(string="Descripción")

    company_id = fields.Many2one(
        'res.company', string="Compañía", required=True,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')

    instructor_id = fields.Many2one(
        'res.users', string="Fisioterapeuta / Responsable", tracking=True)

    # -- Configuración de las clases --
    duration = fields.Float(
        string="Duración (horas)", default=1.0, required=True,
        help="Duración por defecto de cada clase del grupo, en horas.")
    capacity = fields.Integer(
        string="Plazas por clase", default=8, required=True,
        help="Número máximo de pacientes por clase.")

    schedule_line_ids = fields.One2many(
        'physio.group.schedule', 'group_id', string="Horario semanal")

    # -- Facturación / suscripción --
    product_id = fields.Many2one(
        'product.product', string="Producto de cuota",
        default=lambda self: self._default_product_id(),
        domain="[('sale_ok', '=', True)]",
        help="Producto de servicio que se usará en la factura mensual.")
    price = fields.Monetary(
        string="Cuota mensual", currency_field='currency_id',
        help="Importe que se factura cada mes a cada paciente del grupo.")

    # -- Portal / reservas --
    allow_self_booking = fields.Boolean(
        string="Permitir auto-gestión en el portal", default=True,
        help="Si está activo, los pacientes pueden apuntarse/desapuntarse de "
             "sus clases desde el portal.")
    allow_cross_booking = fields.Boolean(
        string="Permitir reservas de otros grupos", default=False,
        help="Si está activo, pacientes de otros grupos pueden ocupar plazas "
             "libres en las clases de este grupo desde el portal.")

    # -- Relaciones / estadísticas --
    membership_ids = fields.One2many(
        'physio.membership', 'group_id', string="Suscripciones")
    active_member_count = fields.Integer(
        string="Pacientes activos", compute='_compute_counts')
    session_ids = fields.One2many(
        'physio.session', 'group_id', string="Clases")
    session_count = fields.Integer(
        string="Nº de clases", compute='_compute_counts')

    @api.model
    def _default_product_id(self):
        product = self.env.ref(
            'amma_physio_groups.product_physio_monthly', raise_if_not_found=False)
        return product.product_variant_id.id if product else False

    @api.depends('membership_ids.state', 'session_ids')
    def _compute_counts(self):
        for group in self:
            group.active_member_count = len(group.membership_ids.filtered(
                lambda m: m.state == 'active'))
            group.session_count = len(group.session_ids)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id and not self.price:
            self.price = self.product_id.lst_price

    # ------------------------------------------------------------------
    # Generación de clases a partir del horario semanal
    # ------------------------------------------------------------------
    def action_open_generate_sessions(self):
        """Abre el asistente para generar clases de un rango de fechas."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Generar clases"),
            'res_model': 'physio.session.generate',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_group_id': self.id},
        }

    def generate_sessions(self, date_from, date_to):
        """Crea las clases del grupo entre dos fechas (incluidas) según su
        horario semanal, evitando duplicados. Devuelve las clases creadas."""
        Session = self.env['physio.session']
        created = Session
        for group in self:
            if not group.schedule_line_ids:
                continue
            existing = set(group.session_ids.mapped(
                lambda s: fields.Datetime.to_string(s.start_datetime)))
            day = date_from
            while day <= date_to:
                for line in group.schedule_line_ids.filtered(
                        lambda l: int(l.weekday) == day.weekday()):
                    start_dt = datetime.combine(
                        day, time(hour=int(line.start_time),
                                  minute=int(round((line.start_time % 1) * 60))))
                    if fields.Datetime.to_string(start_dt) in existing:
                        continue
                    created |= Session.create({
                        'group_id': group.id,
                        'start_datetime': start_dt,
                        'duration': line.duration or group.duration,
                        'capacity': line.capacity or group.capacity,
                    })
                    existing.add(fields.Datetime.to_string(start_dt))
                day += timedelta(days=1)
        return created

    @api.model
    def _cron_generate_sessions(self, weeks_ahead=5):
        """Cron: mantiene generadas las clases de las próximas semanas."""
        date_from = fields.Date.context_today(self)
        date_to = date_from + timedelta(weeks=weeks_ahead)
        groups = self.search([('active', '=', True), ('schedule_line_ids', '!=', False)])
        groups.generate_sessions(date_from, date_to)

    def action_view_sessions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Clases de %s") % self.name,
            'res_model': 'physio.session',
            'view_mode': 'calendar,list,kanban,form',
            'domain': [('group_id', '=', self.id)],
            'context': {'default_group_id': self.id},
        }

    def action_view_members(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Suscripciones de %s") % self.name,
            'res_model': 'physio.membership',
            'view_mode': 'list,form',
            'domain': [('group_id', '=', self.id)],
            'context': {'default_group_id': self.id},
        }
