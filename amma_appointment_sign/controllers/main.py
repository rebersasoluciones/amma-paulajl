# -*- coding: utf-8 -*-
import base64
from datetime import datetime, time

from odoo import fields, http
from odoo.http import request


class AppointmentSignKiosk(http.Controller):

    @http.route(['/appointment/sign/kiosk'],
                type='http', auth='user', website=False)
    def sign_kiosk(self, scope='today', **kw):
        SignRequest = request.env['sign.request'].sudo()
        domain = [('calendar_event_id', '!=', False), ('state', '=', 'sent')]
        if scope == 'today':
            today = fields.Date.context_today(request.env.user)
            domain += [
                ('appointment_start', '>=',
                 fields.Datetime.to_string(datetime.combine(today, time.min))),
                ('appointment_start', '<=',
                 fields.Datetime.to_string(datetime.combine(today, time.max))),
            ]
        requests = SignRequest.search(
            domain, order='appointment_start asc, id asc', limit=200)

        docs = []
        for sign_request in requests:
            item = sign_request.request_item_ids[:1]
            if not item:
                continue
            local = sign_request.appointment_start and fields.Datetime.context_timestamp(
                request.env.user, sign_request.appointment_start)
            docs.append({
                'partner': sign_request.signer_partner_id.name or '',
                'document': sign_request.template_id.display_name,
                'start_str': local.strftime('%H:%M') if local else '',
                'url': "%s/sign/document/%s/%s" % (
                    sign_request.get_base_url(), sign_request.id, item.access_token),
            })
        return request.render('amma_appointment_sign.sign_kiosk_list', {
            'docs': docs,
            'scope': scope,
        })

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
