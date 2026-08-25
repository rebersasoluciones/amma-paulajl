# -*- coding: utf-8 -*-
"""Utilidades compartidas del módulo.

Odoo guarda los campos Datetime en UTC y los muestra en la zona horaria del
usuario. Las horas del horario semanal (y los rangos de fechas del portal) se
escriben en hora local, así que hay que convertirlas antes de guardarlas o de
compararlas contra la base de datos; si no, aparecen desplazadas tantas horas
como marque el huso (p. ej. 09:00 se vería como 11:00 en España en verano).
"""
from pytz import UTC, UnknownTimeZoneError, timezone


def user_timezone(env):
    """Zona horaria en la que el usuario ve las fechas (UTC si no hay ninguna)."""
    tz_name = (env.context.get('tz')
               or env.user.tz
               or env.company.partner_id.tz)
    if not tz_name:
        return UTC
    try:
        return timezone(tz_name)
    except UnknownTimeZoneError:
        return UTC


def local_to_utc(env, naive_local_dt):
    """Convierte una fecha/hora naíf en hora local a la naíf en UTC que guarda Odoo."""
    local_dt = user_timezone(env).localize(naive_local_dt)
    return local_dt.astimezone(UTC).replace(tzinfo=None)
