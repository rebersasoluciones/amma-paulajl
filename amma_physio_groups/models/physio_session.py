# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class PhysioSession(models.Model):
    _name = 'physio.session'
    _description = "Clase de fisioterapia"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_datetime asc'
    _rec_name = 'display_name'

    group_id = fields.Many2one(
        'physio.group', string="Grupo", required=True, ondelete='cascade',
        tracking=True, index=True)
    company_id = fields.Many2one(related='group_id.company_id', store=True)
    color = fields.Integer(related='group_id.color')
    instructor_id = fields.Many2one(related='group_id.instructor_id', store=True)
    allow_cross_booking = fields.Boolean(related='group_id.allow_cross_booking')
    allow_self_booking = fields.Boolean(related='group_id.allow_self_booking')
    booking_cutoff_hours = fields.Integer(related='group_id.booking_cutoff_hours')

    start_datetime = fields.Datetime(
        string="Inicio", required=True, tracking=True, index=True)
    duration = fields.Float(string="Duración (horas)", default=1.0, required=True)
    stop_datetime = fields.Datetime(
        string="Fin", compute='_compute_stop_datetime', store=True)

    capacity = fields.Integer(string="Plazas", default=8, required=True)
    booking_ids = fields.One2many(
        'physio.booking', 'session_id', string="Reservas")
    seats_taken = fields.Integer(
        string="Plazas ocupadas", compute='_compute_seats', store=True)
    seats_available = fields.Integer(
        string="Plazas libres", compute='_compute_seats', store=True)
    is_full = fields.Boolean(
        string="Completa", compute='_compute_seats', store=True)

    state = fields.Selection([
        ('scheduled', "Programada"),
        ('done', "Realizada"),
        ('cancelled', "Cancelada"),
    ], string="Estado", default='scheduled', required=True, tracking=True, index=True)

    @api.depends('start_datetime', 'duration')
    def _compute_stop_datetime(self):
        for session in self:
            if session.start_datetime:
                session.stop_datetime = session.start_datetime + timedelta(
                    hours=session.duration or 0.0)
            else:
                session.stop_datetime = False

    @api.depends('booking_ids.state', 'capacity')
    def _compute_seats(self):
        for session in self:
            taken = len(session.booking_ids.filtered(
                lambda b: b.state in ('booked', 'attended')))
            session.seats_taken = taken
            session.seats_available = max(session.capacity - taken, 0)
            session.is_full = taken >= session.capacity

    @api.depends('group_id.name', 'start_datetime')
    def _compute_display_name(self):
        for session in self:
            if session.start_datetime and session.group_id:
                dt = fields.Datetime.context_timestamp(session, session.start_datetime)
                session.display_name = "%s · %s" % (
                    session.group_id.name, dt.strftime('%d/%m/%Y %H:%M'))
            else:
                session.display_name = session.group_id.name or _("Clase")

    @api.constrains('capacity')
    def _check_capacity(self):
        for session in self:
            if session.capacity < 0:
                raise ValidationError(_("La capacidad no puede ser negativa."))

    # ------------------------------------------------------------------
    # Acciones de estado
    # ------------------------------------------------------------------
    def action_mark_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        template = self.env.ref(
            'amma_physio_groups.mail_template_physio_session_cancelled',
            raise_if_not_found=False)
        for session in self:
            bookings = session.booking_ids.filtered(lambda b: b.state == 'booked')
            partners = bookings.mapped('partner_id')
            bookings.write({'state': 'cancelled'})
            session.state = 'cancelled'
            # Avisa por correo a todos los pacientes que tenían plaza
            if template:
                for partner in partners.filtered(lambda p: p.email):
                    template.send_mail(
                        session.id, force_send=False,
                        email_values={'email_to': partner.email},
                        email_layout_xmlid='mail.mail_notification_light')

    def action_reset_scheduled(self):
        self.write({'state': 'scheduled'})

    # ------------------------------------------------------------------
    # Plaza asignada automática (auto-enrolamiento de los miembros del grupo)
    # ------------------------------------------------------------------
    def _autoenroll_group_members(self):
        """Apunta automáticamente a los pacientes activos del grupo en la clase
        (su plaza reservada), respetando la capacidad y sin duplicar."""
        Booking = self.env['physio.booking']
        for session in self:
            if session.state != 'scheduled':
                continue
            active_bookings = session.booking_ids.filtered(
                lambda b: b.state in ('booked', 'attended'))
            taken_partners = active_bookings.mapped('partner_id')
            taken = len(active_bookings)
            memberships = session.group_id.membership_ids.filtered(
                lambda m: m.state == 'active')
            for membership in memberships:
                if membership.partner_id in taken_partners:
                    continue
                if taken >= session.capacity:
                    break
                Booking.create({
                    'session_id': session.id,
                    'partner_id': membership.partner_id.id,
                    'membership_id': membership.id,
                    'is_cross_booking': False,
                    'state': 'booked',
                })
                taken += 1

    def _is_within_cutoff(self):
        """True si la clase está dentro del plazo de antelación mínima (no se
        puede gestionar desde el portal)."""
        self.ensure_one()
        cutoff = self.booking_cutoff_hours or 0
        if not self.start_datetime or not cutoff:
            return False
        return self.start_datetime - fields.Datetime.now() < timedelta(hours=cutoff)

    # ------------------------------------------------------------------
    # Reservas (usado por el portal)
    # ------------------------------------------------------------------
    def _check_bookable(self, partner):
        """Valida que un paciente pueda apuntarse a esta clase.
        Lanza UserError si no es posible."""
        self.ensure_one()
        if self.state != 'scheduled':
            raise UserError(_("Esta clase no admite reservas."))
        if self.start_datetime and self.start_datetime < fields.Datetime.now():
            raise UserError(_("La clase ya ha comenzado."))
        existing = self.booking_ids.filtered(
            lambda b: b.partner_id == partner and b.state in ('booked', 'attended'))
        if existing:
            raise UserError(_("Ya estás apuntado a esta clase."))
        if self.seats_available <= 0:
            raise UserError(_("La clase está completa."))

    def book_partner(self, partner, membership=False):
        """Crea (o reactiva) una reserva del paciente en la clase."""
        self.ensure_one()
        self._check_bookable(partner)
        cancelled = self.booking_ids.filtered(
            lambda b: b.partner_id == partner and b.state == 'cancelled')
        is_cross = bool(membership) and membership.group_id != self.group_id
        if not membership:
            membership = self.env['physio.membership'].search([
                ('partner_id', '=', partner.id),
                ('state', '=', 'active'),
            ], limit=1)
            is_cross = bool(membership) and membership.group_id != self.group_id
        if cancelled:
            cancelled[0].write({'state': 'booked', 'is_cross_booking': is_cross})
            return cancelled[0]
        return self.env['physio.booking'].create({
            'session_id': self.id,
            'partner_id': partner.id,
            'membership_id': membership.id if membership else False,
            'is_cross_booking': is_cross,
            'state': 'booked',
        })
