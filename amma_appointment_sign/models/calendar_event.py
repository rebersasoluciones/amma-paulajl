# -*- coding: utf-8 -*-
import logging

from odoo import _, Command, api, fields, models

_logger = logging.getLogger(__name__)


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    sign_request_ids = fields.Many2many(
        'sign.request', 'calendar_event_sign_request_rel',
        'event_id', 'request_id', string="Solicitudes de firma", copy=False)
    sign_request_count = fields.Integer(
        compute='_compute_sign_state')
    sign_all_signed = fields.Boolean(
        string="Documentos firmados", compute='_compute_sign_state')
    sign_documents_sent = fields.Boolean(
        string="Documentos enviados", copy=False, readonly=True)

    @api.depends('sign_request_ids.state')
    def _compute_sign_state(self):
        for event in self:
            reqs = event.sign_request_ids.sudo()
            event.sign_request_count = len(reqs)
            event.sign_all_signed = bool(reqs) and all(
                r.state == 'signed' for r in reqs)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _appointment_sign_templates(self):
        self.ensure_one()
        atype = self.appointment_type_id
        return atype.sign_template_ids if atype else self.env['sign.template']

    def _appointment_sign_partner(self):
        """Devuelve el paciente (asistente que no es el organizador)."""
        self.ensure_one()
        organizer = self.user_id.partner_id
        candidates = self.partner_ids.filtered(lambda p: p != organizer)
        return candidates[:1] or self.partner_ids[:1]

    def _ensure_sign_requests(self):
        """Crea las solicitudes de firma que falten (una por documento) para el
        paciente, sin enviar el correo nativo de Firma (usamos el nuestro)."""
        SignRequest = self.env['sign.request'].sudo()
        default_role = self.env.ref(
            'sign.sign_item_role_default', raise_if_not_found=False)
        for event in self:
            templates = event._appointment_sign_templates()
            if not templates:
                continue
            partner = event._appointment_sign_partner()
            if not partner or not partner.email:
                continue
            existing_templates = event.sign_request_ids.mapped('template_id')
            for template in templates - existing_templates:
                role = template.sign_item_ids.responsible_id[:1] or default_role
                if not role:
                    continue
                request = SignRequest.with_context(no_sign_mail=True).create({
                    'template_id': template.id,
                    'reference': "%s - %s" % (template.display_name, partner.name),
                    'subject': _("Documento de tu cita: %s") % template.display_name,
                    'request_item_ids': [Command.create({
                        'partner_id': partner.id,
                        'role_id': role.id,
                        'mail_sent_order': 1,
                    })],
                    'reference_doc': "%s,%s" % (event._name, event.id),
                })
                event.sign_request_ids = [Command.link(request.id)]
        return self.sign_request_ids

    def _sign_signing_url(self, request):
        request = request.sudo()
        item = request.request_item_ids[:1]
        if not item:
            return False
        return "%s/sign/document/%s/%s" % (
            request.get_base_url(), request.id, item.access_token)

    def _sign_download_url(self, request, kind='origin'):
        request = request.sudo()
        return "%s/sign/download/%s/%s/%s" % (
            request.get_base_url(), request.id, request.access_token, kind)

    # ------------------------------------------------------------------
    # Envío de documentos al confirmar la cita
    # ------------------------------------------------------------------
    def _sign_email_links(self):
        """Lista de {'name', 'url'} de firma online para el correo."""
        self.ensure_one()
        links = []
        for request in self.sign_request_ids.sudo():
            url = self._sign_signing_url(request)
            if url:
                links.append({
                    'name': request.template_id.display_name,
                    'url': url,
                })
        return links

    def _sign_blank_attachments(self):
        """Copia los PDF en blanco de las plantillas como adjuntos del correo."""
        self.ensure_one()
        Attachment = self.env['ir.attachment'].sudo()
        attachments = Attachment
        for request in self.sign_request_ids.sudo():
            for document in request.template_id.document_ids:
                source = document.attachment_id
                if not source or not source.datas:
                    continue
                attachments |= Attachment.create({
                    'name': source.name or (document.display_name + '.pdf'),
                    'datas': source.datas,
                    'mimetype': 'application/pdf',
                    'res_model': self._name,
                    'res_id': self.id,
                })
        return attachments

    def _send_appointment_sign_documents(self):
        template = self.env.ref(
            'amma_appointment_sign.mail_template_appointment_documents',
            raise_if_not_found=False)
        for event in self:
            if not event._appointment_sign_templates():
                continue
            event._ensure_sign_requests()
            if not event.sign_request_ids:
                continue
            partner = event._appointment_sign_partner()
            if template and partner and partner.email:
                attachments = event._sign_blank_attachments()
                template.send_mail(
                    event.id, force_send=False,
                    email_layout_xmlid='mail.mail_notification_light',
                    email_values={'attachment_ids': [Command.set(attachments.ids)]})
            event.sign_documents_sent = True

    def action_send_sign_documents(self):
        self._send_appointment_sign_documents()
        return True

    @api.model_create_multi
    def create(self, vals_list):
        events = super().create(vals_list)
        for event in events:
            try:
                atype = event.appointment_type_id
                if atype and atype.sign_auto_send \
                        and atype.sign_template_ids \
                        and not event.sign_documents_sent:
                    event._send_appointment_sign_documents()
            except Exception as error:  # noqa: BLE001
                _logger.warning(
                    "No se pudieron enviar los documentos de firma de la cita "
                    "%s: %s", event.id, error)
        return events

    # ------------------------------------------------------------------
    # Acciones de la ficha
    # ------------------------------------------------------------------
    def action_appointment_sign_qr(self):
        self.ensure_one()
        self._ensure_sign_requests()
        if not self.sign_request_ids:
            return False
        Line = self.env['appointment.sign.qr.line']
        lines = []
        for request in self.sign_request_ids:
            url = self._sign_signing_url(request)
            if not url:
                continue
            lines.append(Command.create({
                'request_id': request.id,
                'name': request.reference,
                'signing_url': url,
                'qr_image': self.env['appointment.sign.qr']._make_qr(url),
                'is_signed': request.sudo().state == 'signed',
            }))
        wizard = self.env['appointment.sign.qr'].create({
            'event_id': self.id,
            'line_ids': lines,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _("Firmar en tablet (QR)"),
            'res_model': 'appointment.sign.qr',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_appointment_sign_qr_fullscreen(self):
        """Abre la página kiosco a pantalla completa con el QR para la tablet."""
        self.ensure_one()
        self._ensure_sign_requests()
        return {
            'type': 'ir.actions.act_url',
            'url': '/appointment/sign/qr/%s' % self.id,
            'target': 'new',
        }

    def action_print_blank_documents(self):
        self.ensure_one()
        self._ensure_sign_requests()
        return self._sign_download_action('origin')

    def action_print_signed_documents(self):
        self.ensure_one()
        return self._sign_download_action('completed')

    def _sign_download_action(self, kind):
        requests = self.sign_request_ids
        if kind == 'completed':
            requests = requests.filtered(lambda r: r.state == 'signed')
        if not requests:
            return False
        if len(requests) == 1:
            return {
                'type': 'ir.actions.act_url',
                'url': self._sign_download_url(requests, kind),
                'target': 'new',
            }
        # Varios documentos: abre la lista de solicitudes para descargar cada una
        return {
            'type': 'ir.actions.act_window',
            'name': _("Documentos"),
            'res_model': 'sign.request',
            'view_mode': 'list,form',
            'domain': [('id', 'in', requests.ids)],
        }

    def action_view_sign_requests(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Solicitudes de firma"),
            'res_model': 'sign.request',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.sign_request_ids.ids)],
        }
