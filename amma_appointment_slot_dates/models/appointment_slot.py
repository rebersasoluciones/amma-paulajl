# -*- coding: utf-8 -*-
from odoo import fields, models


class AppointmentSlot(models.Model):
    _inherit = 'appointment.slot'

    date_start = fields.Date(string="Válido desde")
    date_end = fields.Date(string="Válido hasta")

    _check_validity_dates = models.Constraint(
        'CHECK(date_start IS NULL OR date_end IS NULL OR date_start <= date_end)',
        "La fecha de fin de vigencia no puede ser anterior a la de inicio.",
    )

    def _matches_date(self, day):
        """Si la franja recurrente genera hueco el día indicado (date)."""
        self.ensure_one()
        if self.slot_type != 'recurring':
            return True
        return ((not self.date_start or self.date_start <= day)
                and (not self.date_end or day <= self.date_end))
