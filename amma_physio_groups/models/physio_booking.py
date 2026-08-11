# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PhysioBooking(models.Model):
    _name = 'physio.booking'
    _description = "Reserva / asistencia a clase"
    _order = 'session_start desc'

    session_id = fields.Many2one(
        'physio.session', string="Clase", required=True,
        ondelete='cascade', index=True)
    partner_id = fields.Many2one(
        'res.partner', string="Paciente", required=True, index=True)
    membership_id = fields.Many2one(
        'physio.membership', string="Suscripción", ondelete='set null')

    group_id = fields.Many2one(related='session_id.group_id', store=True)
    company_id = fields.Many2one(related='session_id.company_id', store=True)
    session_start = fields.Datetime(
        related='session_id.start_datetime', store=True, string="Inicio")

    is_cross_booking = fields.Boolean(
        string="Reserva de otro grupo",
        help="La reserva se ha hecho en una clase que no es la del grupo "
             "habitual del paciente.")
    cutoff_locked = fields.Boolean(
        string="Fuera de plazo", compute='_compute_cutoff_locked',
        help="La clase está dentro del plazo de antelación mínima y ya no puede "
             "gestionarse desde el portal.")

    @api.depends('session_start', 'session_id.booking_cutoff_hours')
    def _compute_cutoff_locked(self):
        for booking in self:
            booking.cutoff_locked = bool(booking.session_id) and \
                booking.session_id._is_within_cutoff()

    state = fields.Selection([
        ('booked', "Reservada"),
        ('attended', "Asistió"),
        ('no_show', "No asistió"),
        ('cancelled', "Cancelada"),
    ], string="Estado", default='booked', required=True, index=True)

    @api.depends('partner_id', 'session_id.display_name')
    def _compute_display_name(self):
        for booking in self:
            if booking.partner_id and booking.session_id:
                booking.display_name = "%s · %s" % (
                    booking.partner_id.name, booking.session_id.display_name)
            else:
                booking.display_name = booking.partner_id.name or _("Reserva")

    @api.constrains('partner_id', 'session_id', 'state')
    def _check_unique_active_booking(self):
        for booking in self:
            if booking.state in ('cancelled',):
                continue
            dup = self.search_count([
                ('id', '!=', booking.id),
                ('session_id', '=', booking.session_id.id),
                ('partner_id', '=', booking.partner_id.id),
                ('state', 'in', ('booked', 'attended', 'no_show')),
            ])
            if dup:
                raise ValidationError(_(
                    "El paciente ya tiene una reserva en esta clase."))

    def action_set_attended(self):
        self.write({'state': 'attended'})

    def action_set_no_show(self):
        self.write({'state': 'no_show'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_booked(self):
        self.write({'state': 'booked'})
