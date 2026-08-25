# -*- coding: utf-8 -*-
from odoo import models


class AppointmentType(models.Model):
    _inherit = 'appointment.type'

    def _slots_generate(self, first_day, last_day, timezone, reference_date=None):
        slots = super()._slots_generate(first_day, last_day, timezone, reference_date=reference_date)
        result = []
        for slot_data in slots:
            slot = slot_data['slot']
            if slot.slot_type != 'recurring' or (not slot.date_start and not slot.date_end):
                result.append(slot_data)
                continue
            slot_day = slot_data[self.appointment_tz][0].date()
            if slot._matches_date(slot_day):
                result.append(slot_data)
        return result
