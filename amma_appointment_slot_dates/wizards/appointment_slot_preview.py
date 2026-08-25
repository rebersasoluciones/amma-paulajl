# -*- coding: utf-8 -*-
from datetime import timedelta

from markupsafe import Markup, escape

from odoo import _, api, fields, models
from odoo.tools.misc import format_duration

MAX_PREVIEW_DAYS = 366


class AppointmentSlotPreview(models.TransientModel):
    _name = 'amma.appointment.slot.preview'
    _description = "Vista previa del horario semana a semana"

    def _default_appointment_type_id(self):
        if self.env.context.get('active_model') == 'appointment.type':
            return self.env.context.get('active_id')
        return False

    appointment_type_id = fields.Many2one(
        'appointment.type', string="Tipo de cita", required=True,
        default=_default_appointment_type_id)
    date_start = fields.Date(
        string="Desde", required=True, default=fields.Date.context_today)
    date_end = fields.Date(
        string="Hasta", required=True,
        compute='_compute_date_end', store=True, readonly=False)
    gap_count = fields.Integer(string="Días sin horario", compute='_compute_preview')
    overlap_count = fields.Integer(string="Días con solape", compute='_compute_preview')
    preview_html = fields.Html(compute='_compute_preview', sanitize=False)

    @api.depends('appointment_type_id', 'date_start')
    def _compute_date_end(self):
        for preview in self:
            start = preview.date_start or fields.Date.context_today(preview)
            days = preview.appointment_type_id.max_schedule_days or 15
            preview.date_end = start + timedelta(days=days)

    @api.depends('appointment_type_id.slot_ids', 'appointment_type_id.slot_ids.date_start',
                 'appointment_type_id.slot_ids.date_end', 'date_start', 'date_end')
    def _compute_preview(self):
        for preview in self:
            html, gaps, overlaps = preview._render_preview()
            preview.preview_html = html
            preview.gap_count = gaps
            preview.overlap_count = overlaps

    def _slots_by_day(self):
        """Franjas recurrentes vigentes en cada día del rango, por fecha."""
        self.ensure_one()
        slots = self.appointment_type_id.slot_ids.filtered(
            lambda slot: slot.slot_type == 'recurring')
        days = {}
        day = self.date_start
        while day <= self.date_end and len(days) < MAX_PREVIEW_DAYS:
            weekday_slots = slots.filtered(
                lambda slot: int(slot.weekday) == day.isoweekday() and slot._matches_date(day))
            days[day] = weekday_slots.sorted('start_hour')
            day += timedelta(days=1)
        return days

    def _overlapping_slots(self, slots):
        previous_end = None
        for slot in slots:
            if previous_end is not None and slot.start_hour < previous_end:
                return True
            previous_end = slot._convert_end_hour_24_format()
        return False

    def _render_preview(self):
        self.ensure_one()
        if not (self.appointment_type_id and self.date_start and self.date_end) \
                or self.date_end < self.date_start:
            return False, 0, 0

        days = self._slots_by_day()
        weekday_labels = dict(
            self.env['appointment.slot']._fields['weekday']._description_selection(self.env))
        weekday_used = {
            weekday: any(slots for day, slots in days.items() if day.isoweekday() == weekday)
            for weekday in range(1, 8)
        }

        header = Markup("<th class='text-start'>%s</th>") % _("Semana del")
        header += Markup('').join(
            Markup("<th class='text-center'>%s</th>") % escape(weekday_labels.get(str(weekday), ''))
            for weekday in range(1, 8)
        )

        gaps = overlaps = 0
        rows = []
        for monday in sorted({day - timedelta(days=day.weekday()) for day in days}):
            cells = Markup("<td class='text-start text-muted'>%s</td>") % escape(
                monday.strftime('%d/%m/%Y'))
            for offset in range(7):
                day = monday + timedelta(days=offset)
                if day not in days:
                    cells += Markup("<td></td>")
                    continue
                slots = days[day]
                if not slots:
                    is_gap = weekday_used.get(day.isoweekday())
                    gaps += 1 if is_gap else 0
                    cells += Markup("<td class='text-center %s'>—</td>") % (
                        'table-warning' if is_gap else 'text-muted')
                    continue
                is_overlap = self._overlapping_slots(slots)
                overlaps += 1 if is_overlap else 0
                hours = Markup("<br/>").join(
                    escape("%s - %s" % (format_duration(slot.start_hour),
                                        format_duration(slot.end_hour)))
                    for slot in slots
                )
                cells += Markup("<td class='text-center %s'>%s</td>") % (
                    'table-danger' if is_overlap else '', hours)
            rows.append(Markup("<tr>%s</tr>") % cells)

        table = Markup(
            "<table class='table table-sm table-bordered'>"
            "<thead><tr>%s</tr></thead><tbody>%s</tbody></table>"
        ) % (header, Markup('').join(rows))
        return table, gaps, overlaps
