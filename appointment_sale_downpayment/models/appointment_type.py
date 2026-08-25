# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AppointmentType(models.Model):
    _inherit = 'appointment.type'

    downpayment_prepayment_percent = fields.Float(
        string="Anticipo",
        default=lambda self: self.env.company.prepayment_percent,
        help="Parte del precio del servicio que el paciente paga al reservar. "
             "Con el 100% se cobra todo por adelantado. La cita se confirma en "
             "cuanto se paga esta parte; el resto se factura después desde el "
             "mismo pedido de venta.")

    @api.constrains('has_payment_step', 'downpayment_prepayment_percent')
    def _check_downpayment_prepayment_percent(self):
        for appointment_type in self:
            if appointment_type.has_payment_step and not (
                    0 < appointment_type.downpayment_prepayment_percent <= 1.0):
                raise ValidationError(_(
                    "El anticipo de «%(name)s» tiene que ser mayor que 0 y como "
                    "mucho el 100%%.",
                    name=appointment_type.name,
                ))
