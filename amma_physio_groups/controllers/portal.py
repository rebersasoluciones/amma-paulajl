# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import _, fields, http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class PhysioPortal(CustomerPortal):

    # ------------------------------------------------------------------
    # Contadores en /my (portada del portal)
    # ------------------------------------------------------------------
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        if 'physio_membership_count' in counters:
            values['physio_membership_count'] = request.env['physio.membership'].search_count(
                [('partner_id', '=', partner.id), ('state', '=', 'active')])
        return values

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _physio_partner(self):
        return request.env.user.partner_id

    def _physio_active_memberships(self):
        return request.env['physio.membership'].search([
            ('partner_id', '=', self._physio_partner().id),
            ('state', '=', 'active'),
        ])

    def _physio_my_bookings(self, upcoming_only=True):
        domain = [('partner_id', '=', self._physio_partner().id),
                  ('state', '=', 'booked')]
        if upcoming_only:
            domain.append(('session_start', '>=', fields.Datetime.now()))
        return request.env['physio.booking'].search(domain, order='session_start asc')

    def _physio_bookable_sessions(self, memberships, days=21):
        """Devuelve las clases futuras a las que el paciente puede apuntarse."""
        if not memberships:
            return request.env['physio.session']
        partner = self._physio_partner()
        my_group_ids = memberships.mapped('group_id').ids
        date_to = fields.Datetime.now() + timedelta(days=days)

        # Se leen en sudo para que el cálculo de plazas libres sea real
        # (la regla de registro del portal sólo dejaría ver las reservas propias).
        Session = request.env['physio.session'].sudo()
        candidates = Session.search([
            ('state', '=', 'scheduled'),
            ('start_datetime', '>=', fields.Datetime.now()),
            ('start_datetime', '<=', date_to),
        ], order='start_datetime asc')

        already_booked = set(self._physio_my_bookings().mapped('session_id').ids)
        result = Session
        for session in candidates:
            if session.id in already_booked:
                continue
            if session.seats_available <= 0:
                continue
            own = session.group_id.id in my_group_ids
            if own and session.group_id.allow_self_booking:
                result |= session
            elif not own and session.group_id.allow_cross_booking:
                result |= session
        return result

    # ------------------------------------------------------------------
    # Página principal del paciente
    # ------------------------------------------------------------------
    @http.route(['/my/physio'], type='http', auth='user', website=True)
    def portal_physio_home(self, **kw):
        memberships = self._physio_active_memberships()
        bookings = self._physio_my_bookings()
        bookable = self._physio_bookable_sessions(memberships)

        # Facturas pendientes de pago
        invoices = request.env['account.move'].search([
            ('partner_id', '=', self._physio_partner().id),
            ('physio_membership_id', '!=', False),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ('not_paid', 'partial')),
        ])

        values = {
            'page_name': 'physio',
            'memberships': memberships,
            'bookings': bookings,
            'bookable_sessions': bookable,
            'open_invoices': invoices,
        }
        return request.render('amma_physio_groups.portal_physio_home', values)

    # ------------------------------------------------------------------
    # Apuntarse a una clase
    # ------------------------------------------------------------------
    @http.route(['/my/physio/session/<int:session_id>/book'],
                type='http', auth='user', website=True, methods=['POST'])
    def portal_physio_book(self, session_id, **kw):
        partner = self._physio_partner()
        memberships = self._physio_active_memberships()
        session = request.env['physio.session'].browse(session_id).exists()

        if not session or not memberships:
            return request.redirect('/my/physio?booking_error=1')

        my_group_ids = memberships.mapped('group_id').ids
        own = session.group_id.id in my_group_ids
        allowed = (own and session.group_id.allow_self_booking) or \
                  (not own and session.group_id.allow_cross_booking)
        if not allowed:
            return request.redirect('/my/physio?booking_error=1')

        # Membresía de referencia (la del grupo si existe, si no la primera activa)
        membership = memberships.filtered(
            lambda m: m.group_id == session.group_id)[:1] or memberships[:1]
        try:
            session.sudo().book_partner(partner, membership=membership.sudo())
        except (UserError, ValidationError, AccessError):
            return request.redirect('/my/physio?booking_error=1')
        return request.redirect('/my/physio?booking_ok=1')

    # ------------------------------------------------------------------
    # Desapuntarse de una clase
    # ------------------------------------------------------------------
    @http.route(['/my/physio/booking/<int:booking_id>/cancel'],
                type='http', auth='user', website=True, methods=['POST'])
    def portal_physio_cancel(self, booking_id, **kw):
        partner = self._physio_partner()
        booking = request.env['physio.booking'].browse(booking_id).exists()
        if not booking or booking.partner_id != partner:
            return request.redirect('/my/physio?booking_error=1')
        if not booking.session_id.group_id.allow_self_booking:
            return request.redirect('/my/physio?booking_error=1')
        if booking.session_start and booking.session_start < fields.Datetime.now():
            return request.redirect('/my/physio?booking_error=1')
        booking.sudo().action_cancel()
        return request.redirect('/my/physio?cancel_ok=1')
