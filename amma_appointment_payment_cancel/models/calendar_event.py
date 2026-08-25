# -*- coding: utf-8 -*-
from markupsafe import Markup, escape

from odoo import _, fields, models

REFUND_ACTIVITY_XMLID = 'amma_appointment_payment_cancel.mail_activity_type_refund_note'


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    def action_cancel_meeting(self, partner_ids):
        res = super().action_cancel_meeting(partner_ids)
        self._schedule_refund_activity()
        return res

    def _get_paid_documents(self):
        """ Factura o pedido donde está cobrada la cita. """
        self.ensure_one()
        bookings = self.env['calendar.booking'].sudo().search([
            ('calendar_event_id', '=', self.id),
        ])
        invoices = bookings.account_move_id.filtered(
            lambda move: move.state == 'posted')
        orders = bookings.order_line_id.order_id.filtered(
            lambda order: order.amount_paid > 0)
        invoices |= orders.invoice_ids.filtered(
            lambda move: move.state == 'posted')
        return invoices or orders

    def _schedule_refund_activity(self):
        activity_type = self.env.ref(REFUND_ACTIVITY_XMLID, raise_if_not_found=False)
        if not activity_type:
            return
        Activity = self.env['mail.activity'].sudo()
        for event in self:
            for document in event.sudo()._get_paid_documents():
                if Activity.search_count([
                    ('res_model', '=', document._name),
                    ('res_id', '=', document.id),
                    ('activity_type_id', '=', activity_type.id),
                ], limit=1):
                    continue
                document.sudo().activity_schedule(
                    activity_type_id=activity_type.id,
                    user_id=event.user_id.id,
                    note=event._get_refund_activity_note(),
                )

    def _get_refund_activity_note(self):
        self.ensure_one()
        hours_left = (self.start - fields.Datetime.now()).total_seconds() / 3600
        if hours_left >= self.appointment_type_id.min_cancellation_hours:
            message = _(
                "Cita cancelada dentro de plazo: %(name)s (%(start)s). Procede "
                "devolver el importe cobrado al paciente.",
                name=self.name,
                start=self.display_time,
            )
        else:
            message = _(
                "Cita cancelada fuera de plazo: %(name)s (%(start)s). Revisar si "
                "procede devolver el importe cobrado al paciente.",
                name=self.name,
                start=self.display_time,
            )
        return Markup("<p>%s</p>") % escape(message)
