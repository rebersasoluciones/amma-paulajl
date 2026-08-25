# Citas – Vigencia por fechas en disponibilidad recurrente

Cada franja del horario semanal de un tipo de cita puede llevar un rango de
fechas **opcional**:

- **con fechas** → la franja sólo genera huecos dentro de ese rango;
- **sin fechas** → la franja aplica siempre, igual que hasta ahora.

Sirve para que un mismo día de la semana tenga horarios distintos según el
periodo (temporada, semanas alternas, una baja) sin duplicar el tipo de cita y
sin acortar la ventana de reserva.

## Cómo funciona

`appointment.slot` gana `date_start` / `date_end` (con constraint SQL de orden) y
un helper `_matches_date(day)`.

`appointment.type._slots_generate()` se sobrescribe llamando a `super()` y
**filtrando la lista resultante**: para cada hueco, si su franja es recurrente y
tiene fechas, se compara el día del hueco (`slot_data[appointment_tz][0].date()`)
con la vigencia. No se copia el método del core.

## Uso

En el tipo de cita, pestaña *Disponibilidades*, columna **Vigencia** (rango en una
sola columna; se puede dejar vacía).

Ejemplo de dos periodos para el mismo día:

| Cada | Desde | Hasta | Vigencia |
|---|---|---|---|
| Lunes | 09:00 | 13:00 | → 30/09/2026 |
| Lunes | 10:00 | 14:00 | 01/10/2026 → |

## Tras instalar

Subir **"Permitir reservas dentro de los próximos X días"** (`max_schedule_days`)
a 90 en el tipo de cita para tener ventana de 3 meses. Es configuración del
usuario, el módulo no la toca.

## Vista previa del horario

En la pestaña *Disponibilidades*, el botón **Vista previa del horario** abre una
tabla semana a semana de toda la ventana de reserva: una fila por semana, una
columna por día, y en cada celda las franjas que aplican ese día.

- **Ámbar**: ese día no tiene ninguna franja vigente, aunque ese día de la semana
  sí tiene horario en otras fechas del rango. Es el aviso de que un periodo
  termina antes de que empiece el siguiente.
- **Rojo**: dos franjas del mismo día se solapan. Normalmente es un periodo
  antiguo al que se le olvidó poner fecha de fin.

Muestra qué franjas aplican, no los huecos libres: no tiene en cuenta ausencias,
reservas ya hechas ni la antelación mínima.

## Cuidado con esto

- Una franja **sin fecha de fin sigue vigente para siempre**. Al abrir un periodo
  nuevo hay que cerrar el anterior, o convivirán los dos y el día tendrá las
  franjas de ambos.
- Si en un tramo de la ventana de reserva **ningún** slot de ese día está vigente,
  ese día deja de ofrecer huecos sin ningún aviso. Conviene repasar la ventana
  completa después de tocar las fechas.

Licencia: LGPL-3. Autor: Lógica Consultores 360.
