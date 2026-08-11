# Citas – Documentos y Firma en consulta (Odoo 19 EE)

Módulo **independiente** (no tiene relación con el de grupos/clases) para el flujo
de **citas presenciales**: asocia documentos a firmar a cada tipo de cita, los
envía al confirmar, permite firmar por **QR en tablet** e imprimir el PDF en
blanco y el firmado.

## Requisitos
Apps de Enterprise: **Citas** (`appointment`) y **Firma** (`sign`).

## Funcionalidades
- **Documentos por tipo de cita**: en *Citas → Tipo de cita* añade las plantillas
  de *Firma* que el paciente debe firmar (campo **"Documentos a firmar"**), y si
  se envían automáticamente al confirmar.
- **Envío automático al confirmar**: al crearse/confirmarse la cita se envía al
  paciente un **correo** (registrado en el chatter) con:
  - los **PDF en blanco adjuntos** (para imprimir y traer rellenos), y
  - un **botón "Firmar" por documento** para firmar online.
- **Firmar en tablet (QR)**: botón **"Firmar (QR)"** en la cita → muestra un
  **código QR por documento**; el paciente lo escanea con la tablet (o su móvil)
  y firma. La firma queda enlazada a la cita.
- **Imprimir**: botones **"Imprimir en blanco"** y **"Imprimir firmado"** en la
  cita (y por documento en el asistente de QR).

## Cómo funciona (técnico)
- `appointment.type`: `sign_template_ids`, `sign_auto_send`.
- `calendar.event`: al crear con un tipo de cita con documentos, genera
  `sign.request` (una por documento, sin correo nativo de Firma) enlazadas por
  `reference_doc`, y envía el correo propio con adjuntos + enlaces de firma.
- Las URL de firma usan la ruta pública `/sign/document/<id>/<token>`; las de
  descarga `/sign/download/<id>/<token>/origin|completed`.
- El QR se genera en el servidor con el generador de códigos de barras de Odoo.

## Uso
1. Configura una **plantilla de documento** en la app *Firma* (sube el PDF y
   coloca los campos de firma).
2. En el **tipo de cita**, añádela en *Documentos a firmar*.
3. Cuando un paciente reserve/confirme la cita, recibirá el correo con los
   documentos. En consulta, abre la cita y pulsa **"Firmar (QR)"** para que
   firme en la tablet, o **"Imprimir…"** según necesites.

Licencia: LGPL-3. Autor: Rebersa Soluciones.
