# -*- coding: utf-8 -*-
import base64

from odoo import http
from odoo.http import request


class AppointmentSignKiosk(http.Controller):

    @http.route(['/appointment/sign/qr/<int:event_id>'],
                type='http', auth='user', website=False)
    def sign_qr_fullscreen(self, event_id, **kw):
        event = request.env['calendar.event'].browse(event_id).exists()
        if not event:
            return request.not_found()
        event = event.sudo()
        event._ensure_sign_requests()

        docs = []
        for sign_request in event.sign_request_ids:
            url = event._sign_signing_url(sign_request)
            if not url:
                continue
            qr = ''
            try:
                png = request.env['ir.actions.report'].sudo().barcode(
                    'QR', url, width=500, height=500, humanreadable=0)
                qr = base64.b64encode(png).decode()
            except Exception:  # noqa: BLE001
                qr = ''
            docs.append({
                'name': sign_request.template_id.display_name,
                'qr': qr,
                'signed': sign_request.state == 'signed',
            })

        return request.render('amma_appointment_sign.sign_qr_fullscreen', {
            'event': event,
            'docs': docs,
        })
