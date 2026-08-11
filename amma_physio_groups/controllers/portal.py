# -*- coding: utf-8 -*-
from datetime import datetime, time, timedelta

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

    def _physio_bookable_sessions(self, memberships, days=7):
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
            if session._is_within_cutoff():
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
            'no_breadcrumbs': True,
            'memberships': memberships,
            'bookings': bookings,
            'bookable_sessions': bookable,
            'open_invoices': invoices,
        }
        return request.render('amma_physio_groups.portal_physio_home', values)

    def _physio_redirect(self, kw, status):
        """Redirige a la página de origen (portada o planning semanal) con el
        mensaje de estado. Solo se aceptan rutas internas del portal."""
        target = kw.get('redirect') or '/my/physio'
        if not target.startswith('/my/physio'):
            target = '/my/physio'
        sep = '&' if '?' in target else '?'
        return request.redirect('%s%s%s=1' % (target, sep, status))

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
            return self._physio_redirect(kw, 'booking_error')

        my_group_ids = memberships.mapped('group_id').ids
        own = session.group_id.id in my_group_ids
        allowed = (own and session.group_id.allow_self_booking) or \
                  (not own and session.group_id.allow_cross_booking)
        if not allowed:
            return self._physio_redirect(kw, 'booking_error')

        # Regla de antelación mínima (p. ej. 24h antes de la clase)
        if session.sudo()._is_within_cutoff():
            return self._physio_redirect(kw, 'cutoff_error')

        # Tope máximo de clases al mes por paciente
        membership = memberships.filtered(
            lambda m: m.group_id == session.group_id)[:1] or memberships[:1]
        if self._physio_month_limit_reached(partner, memberships, session):
            return self._physio_redirect(kw, 'limit_error')

        try:
            session.sudo().book_partner(partner, membership=membership.sudo())
        except (UserError, ValidationError, AccessError):
            return self._physio_redirect(kw, 'booking_error')
        return self._physio_redirect(kw, 'booking_ok')

    def _physio_month_limit_reached(self, partner, memberships, session):
        """True si el paciente ya alcanzó su tope de clases del mes."""
        limit = max(memberships.mapped('max_classes_per_month') or [0])
        if not limit:
            return False
        local = fields.Datetime.context_timestamp(session, session.start_datetime)
        month_start = datetime(local.year, local.month, 1)
        if local.month == 12:
            month_end = datetime(local.year + 1, 1, 1)
        else:
            month_end = datetime(local.year, local.month + 1, 1)
        count = request.env['physio.booking'].search_count([
            ('partner_id', '=', partner.id),
            ('state', 'in', ('booked', 'attended')),
            ('session_start', '>=', fields.Datetime.to_string(month_start)),
            ('session_start', '<', fields.Datetime.to_string(month_end)),
        ])
        return count >= limit

    # ------------------------------------------------------------------
    # Desapuntarse de una clase
    # ------------------------------------------------------------------
    @http.route(['/my/physio/booking/<int:booking_id>/cancel'],
                type='http', auth='user', website=True, methods=['POST'])
    def portal_physio_cancel(self, booking_id, **kw):
        partner = self._physio_partner()
        booking = request.env['physio.booking'].browse(booking_id).exists()
        if not booking or booking.partner_id != partner:
            return self._physio_redirect(kw, 'booking_error')
        if not booking.session_id.group_id.allow_self_booking:
            return self._physio_redirect(kw, 'booking_error')
        if booking.session_start and booking.session_start < fields.Datetime.now():
            return self._physio_redirect(kw, 'booking_error')
        # Regla de antelación mínima (p. ej. 24h antes de la clase)
        if booking.session_id.sudo()._is_within_cutoff():
            return self._physio_redirect(kw, 'cutoff_error')
        booking.sudo().action_cancel()
        return self._physio_redirect(kw, 'cancel_ok')

    # ------------------------------------------------------------------
    # Vista semanal tipo WODBUSTER (scroll por semanas)
    # ------------------------------------------------------------------
    @http.route(['/my/physio/semana'], type='http', auth='user', website=True)
    def portal_physio_week(self, week=0, **kw):
        try:
            week = int(week)
        except (TypeError, ValueError):
            week = 0
        # Límite de navegación: 8 semanas hacia adelante, 4 hacia atrás
        week = max(-4, min(8, week))
        partner = self._physio_partner()
        memberships = self._physio_active_memberships()
        my_group_ids = memberships.mapped('group_id').ids

        today = fields.Date.context_today(self)
        monday = today - timedelta(days=today.weekday()) + timedelta(weeks=week)
        sunday = monday + timedelta(days=6)
        start_dt = datetime.combine(monday, time.min)
        end_dt = datetime.combine(sunday, time.max)

        Session = request.env['physio.session'].sudo()
        sessions = Session.search([
            ('state', '=', 'scheduled'),
            ('start_datetime', '>=', fields.Datetime.to_string(start_dt)),
            ('start_datetime', '<=', fields.Datetime.to_string(end_dt)),
        ], order='start_datetime asc')

        my_bookings = request.env['physio.booking'].search([
            ('partner_id', '=', partner.id),
            ('state', '=', 'booked'),
            ('session_start', '>=', fields.Datetime.to_string(start_dt)),
            ('session_start', '<=', fields.Datetime.to_string(end_dt)),
        ])
        booking_by_session = {b.session_id.id: b for b in my_bookings}

        buckets = {monday + timedelta(days=i): [] for i in range(7)}
        for session in sessions:
            local = fields.Datetime.context_timestamp(session, session.start_datetime)
            day = local.date()
            if day not in buckets:
                continue
            own = session.group_id.id in my_group_ids
            if not (own or session.group_id.allow_cross_booking):
                continue
            booking = booking_by_session.get(session.id)
            buckets[day].append({
                'session': session,
                'booking': booking,
                'own': own,
                'time': local.strftime('%H:%M'),
                'bookable': (not booking) and session.seats_available > 0
                and not session._is_within_cutoff()
                and ((own and session.group_id.allow_self_booking)
                     or (not own and session.group_id.allow_cross_booking)),
            })

        weekday_es = ['Lunes', 'Martes', 'Miércoles', 'Jueves',
                      'Viernes', 'Sábado', 'Domingo']
        days = [{
            'date': d,
            'label': weekday_es[d.weekday()],
            'is_today': d == today,
            'sessions': buckets[d],
        } for d in sorted(buckets)]
        values = {
            'page_name': 'physio',
            'no_breadcrumbs': True,
            'memberships': memberships,
            'days': days,
            'week': week,
            'monday': monday,
            'sunday': sunday,
            'redirect': '/my/physio/semana?week=%s' % week,
        }
        return request.render('amma_physio_groups.portal_physio_week', values)
