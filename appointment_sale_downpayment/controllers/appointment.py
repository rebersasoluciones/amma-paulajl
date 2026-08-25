# -*- coding: utf-8 -*-
from odoo import Command
from odoo.http import request

from odoo.addons.appointment_account_payment.controllers.appointment import AppointmentAccountPayment


class AppointmentSaleDownpayment(AppointmentAccountPayment):

    def _redirect_to_payment(self, calendar_booking):
        """ Override: en vez de facturar la reserva (o meterla en el carrito de la
            tienda, que cobra el 100%), se crea un pedido de venta con anticipo y se
            lleva al paciente al portal del pedido, que cobra sólo ese anticipo. """
        order_sudo = self._prepare_downpayment_order(calendar_booking)
        return request.redirect(order_sudo.get_portal_url())

    def _prepare_downpayment_order(self, calendar_booking):
        appointment_type = calendar_booking.appointment_type_id
        tz = (request.session.get('timezone')
              or request.env.context.get('tz')
              or appointment_type.appointment_tz)
        booking_sudo = calendar_booking.sudo()
        return request.env['sale.order'].sudo().create({
            'partner_id': booking_sudo.partner_id.id,
            'prepayment_percent': appointment_type.downpayment_prepayment_percent,
            'require_payment': True,
            'require_signature': False,
            'order_line': [Command.create({
                'product_id': booking_sudo.product_id.id,
                'product_uom_qty': booking_sudo.asked_capacity or 1,
                'name': booking_sudo.with_context(
                    tz=tz, lang=booking_sudo.partner_id.lang)._get_description(),
                'calendar_booking_ids': [Command.link(booking_sudo.id)],
            })],
        })
