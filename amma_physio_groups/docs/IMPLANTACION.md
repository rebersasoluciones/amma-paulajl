# Proceso de implantación limpio

Guía paso a paso para poner en producción el módulo **amma_physio_groups** en una
clínica de fisioterapia.

## 1. Requisitos previos
- Odoo **19.0** (Community o Enterprise).
- Módulos base disponibles (se instalan como dependencias):
  `mail`, `contacts`, `product`, `account`, `account_payment`, `portal`, `website`.

## 2. Instalación
1. Copia la carpeta `amma_physio_groups/` en tu ruta de *addons*.
2. Reinicia el servicio Odoo y **actualiza la lista de aplicaciones**.
3. Instala **“Fisioterapia - Gestión de Grupos y Clases”**.
   - Para probar con datos de ejemplo, activa el *modo demo* al crear la BD.

## 3. Configuración inicial (una sola vez)
1. **Usuarios y permisos**
   - Asigna a recepción el rol *Fisioterapia / Recepción*.
   - Asigna al responsable el rol *Fisioterapia / Responsable*.
2. **Facturación**
   - Configura la compañía (nombre, NIF, dirección, logo) y el diario de ventas.
   - Revisa el producto **“Cuota mensual fisioterapia”** (o crea uno por grupo).
3. **Pagos**
   - *Ajustes → Facturación*: activa **Pago desde el portal** y al menos un
     proveedor de pago (Stripe, redsys, transferencia, etc.).
   - Crea un diario de **Efectivo** para los pagos en mano.
4. **Correo saliente**: configura el servidor SMTP para el envío de cobros.

## 4. Alta de datos maestros
1. **Grupos** (*Fisioterapia → Grupos*)
   - Define nombre, fisioterapeuta, capacidad, duración y **cuota mensual**.
   - Añade el **horario semanal** (día + hora) de cada grupo.
   - En *Portal / Reservas* decide si permites auto-gestión y reservas cruzadas.
2. **Generar clases**
   - Desde el grupo, botón **“Generar clases”** → elige el rango (p. ej. el mes).
   - El cron *Generar clases del periodo* las mantiene creadas automáticamente.
3. **Pacientes** (*Fisioterapia → Pacientes*)
   - Alta con nombre, teléfono y correo (se guardan como contactos).

## 5. Suscripciones y cobros
1. Crea la **suscripción** del paciente a su grupo y pulsa **Activar**.
2. La factura mensual se genera automáticamente (cron diario) o manualmente con
   **“Facturar ahora”**; el paciente recibe el correo con el botón **Pagar**.
3. En *Cobros* puedes **generar un enlace de pago** o **registrar efectivo**.

## 6. Portal del paciente
1. Concede acceso al portal a cada paciente (*Contacto → Conceder acceso al portal*).
2. El paciente entra en `/my/physio` para ver su grupo, apuntarse/desapuntarse de
   clases y pagar sus cuotas.

## 7. Puesta en marcha (checklist)
- [ ] Roles asignados.
- [ ] Diario de ventas y de efectivo configurados.
- [ ] Proveedor de pago + pago desde el portal activos.
- [ ] SMTP configurado y probado.
- [ ] Grupos con horario y cuota.
- [ ] Clases generadas para el mes en curso.
- [ ] Un paciente de prueba con suscripción activa y acceso al portal.
- [ ] Crons activos (*Ajustes → Técnico → Acciones planificadas*).

## 8. Mantenimiento
- Revisa semanalmente *Cobros* para el estado de los pagos.
- El cron de generación de clases evita duplicados; puedes ajustar el horizonte
  (`weeks_ahead`) o su frecuencia.
- Los cambios de grupo se hacen con **“Cambiar de grupo”** desde la suscripción.
