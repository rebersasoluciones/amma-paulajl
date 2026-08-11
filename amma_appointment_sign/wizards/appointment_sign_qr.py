# -*- coding: utf-8 -*-
import base64
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class AppointmentSignQr(models.TransientModel):
    _name = 'appointment.sign.qr'
    _description = "Firmar documentos de la cita por QR"

    event_id = fields.Many2one('calendar.event', string="Cita", readonly=True)
    line_ids = fields.One2many(
        'appointment.sign.qr.line', 'wizard_id', string="Documentos")

    @staticmethod
    def _qr_bytes(env, value):
        """Genera el PNG del código QR para un texto. Devuelve base64 o False."""
        try:
            png = env['ir.actions.report'].barcode(
                'QR', value, width=300, height=300, humanreadable=0)
            return base64.b64encode(png)
        except Exception as error:  # noqa: BLE001
            _logger.warning("No se pudo generar el QR: %s", error)
            return False

    def _make_qr(self, value):
        return self._qr_bytes(self.env, value)


class AppointmentSignQrLine(models.TransientModel):
    _name = 'appointment.sign.qr.line'
    _description = "Documento a firmar (QR)"

    wizard_id = fields.Many2one(
        'appointment.sign.qr', required=True, ondelete='cascade')
    request_id = fields.Many2one('sign.request', string="Solicitud de firma")
    name = fields.Char(string="Documento")
    signing_url = fields.Char(string="Enlace de firma")
    qr_image = fields.Binary(string="Código QR")
    is_signed = fields.Boolean(string="Firmado")

    def action_print_blank(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self.request_id.get_base_url() + '/sign/download/%s/%s/origin' % (
                self.request_id.id, self.request_id.sudo().access_token),
            'target': 'new',
        }

    def action_print_signed(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self.request_id.get_base_url() + '/sign/download/%s/%s/completed' % (
                self.request_id.id, self.request_id.sudo().access_token),
            'target': 'new',
        }
