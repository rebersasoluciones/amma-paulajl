# -*- coding: utf-8 -*-
from odoo.addons.appointment.controllers.calendar import AppointmentCalendarController
from odoo.addons.appointment_account_payment.controllers.calendar import AppointmentAccountPaymentCalendarController


class AppointmentPaymentCancel(AppointmentAccountPaymentCalendarController):

    def _get_prevent_cancel_status(self, event):
        """ Override: sustituye el bloqueo incondicional de las citas pagadas por
            el plazo de horas que se aplica al resto de citas. """
        status = super()._get_prevent_cancel_status(event)
        if status != 'no_cancel_paid':
            return status
        return AppointmentCalendarController._get_prevent_cancel_status(self, event)
