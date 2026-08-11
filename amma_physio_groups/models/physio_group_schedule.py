# -*- coding: utf-8 -*-
from odoo import api, fields, models


WEEKDAYS = [
    ('0', "Lunes"),
    ('1', "Martes"),
    ('2', "Miércoles"),
    ('3', "Jueves"),
    ('4', "Viernes"),
    ('5', "Sábado"),
    ('6', "Domingo"),
]


class PhysioGroupSchedule(models.Model):
    _name = 'physio.group.schedule'
    _description = "Horario semanal del grupo"
    _order = 'weekday, start_time'

    group_id = fields.Many2one(
        'physio.group', string="Grupo", required=True, ondelete='cascade')
    weekday = fields.Selection(WEEKDAYS, string="Día", required=True, default='0')
    start_time = fields.Float(
        string="Hora de inicio", required=True, default=9.0,
        help="Hora del día en formato 24h (p. ej. 9.5 = 09:30).")
    duration = fields.Float(
        string="Duración (horas)",
        help="Si se deja a 0 se usa la duración por defecto del grupo.")
    capacity = fields.Integer(
        string="Plazas",
        help="Si se deja a 0 se usa la capacidad por defecto del grupo.")

    _unique_slot = models.Constraint(
        'unique(group_id, weekday, start_time)',
        "Ya existe una franja para ese grupo, día y hora.")

    @api.depends('weekday', 'start_time')
    def _compute_display_name(self):
        labels = dict(WEEKDAYS)
        for line in self:
            hour = int(line.start_time)
            minute = int(round((line.start_time % 1) * 60))
            line.display_name = "%s %02d:%02d" % (
                labels.get(line.weekday, ''), hour, minute)
