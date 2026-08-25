# Historia clínica

Lo que el fisio ve al abrir un paciente, dentro del propio contacto de Odoo.

## Qué añade

**1. Ficha del paciente** — pestaña *Historia clínica* del contacto:

| Campo | Para qué |
|---|---|
| Es paciente | Marca el contacto como paciente; sin esto no aparece nada más |
| Motivo de consulta | Suelo pélvico, pediatría, entrenamiento… (configurable) |
| Fecha de nacimiento / Edad | La edad se calcula sola |
| Sexo | |
| Profesional responsable | |
| Alertas importantes | Se pinta **en rojo arriba del todo** de la ficha, antes que nada |
| Primera visita / Última visita / Visitas | Calculado de las citas, no se rellena a mano |

Nombre, DNI (`NIF`) y teléfono ya son campos nativos del contacto; no se duplican.

**2. Historial de reservas** — pestaña con todas las citas del paciente, de la
más reciente a la más antigua, con tipo de cita, profesional y estado
(*reservada*, *asistió*, *no se presentó*, *cancelada*). Las canceladas siguen
apareciendo. Cada línea tiene un botón que abre el **registro de esa sesión**.

**3. Registro de sesión** (`amma.clinical.note`) — una anotación por visita:
fecha, profesional, cita, plantilla, el texto del registro y ficheros adjuntos.

**4. Plantillas por tipo de cita** — cada plantilla
(`amma.clinical.note.type`) lleva su guion y los tipos de cita a los que
aplica. Al abrir el registro de una cita, se propone la plantilla de su tipo de
cita y se carga su guion. Vienen dos de partida, *Primera sesión* y *Sesión de
tratamiento*, con los apartados vacíos para que los rellene la clínica.

**5. Permisos** — todo lo clínico está detrás del grupo *Personal clínico*
(*Ajustes → Usuarios*, privilegio **Historia clínica**). Quien no lo tenga no ve
la pestaña, ni los registros, ni el menú. *Responsable* añade configurar
plantillas y borrar registros.

## Menú

**Historia clínica** → Pacientes · Registros de sesión · Configuración
(plantillas y motivos de consulta).

## Del documento de diseño, lo que NO está hecho

- **Apartados de la historia** (sección 3 del documento): estaba marcado *"por
  hacer por mí"*. El mecanismo está listo — se escriben como plantilla de cada
  tipo de cita — pero el contenido clínico lo tiene que definir la clínica.
- **Campos por tipo de tratamiento** (las pestañas *Facial*, *Podología*,
  *Seguimiento* del programa de las capturas): aquí el registro es un texto con
  guion, no campos separados por tratamiento. Cuando estén definidos los
  apartados se decide si basta con la plantilla o hacen falta campos propios.
- **Portal del paciente** (sección 5): el paciente todavía no ve su historial de
  reservas ni las historias que se le compartan. Los pagos y facturas sí los ve
  ya, con el portal nativo. Falta la página de portal y el permiso por registro
  («sólo las que yo dé acceso, no por defecto»).
- **Documentos y consentimientos**: los consentimientos ya los gestiona
  `amma_appointment_sign` desde el tipo de cita. Aquí sólo hay adjuntos por
  registro de sesión.
- **Contabilidad**: los botones nativos del contacto (facturas, pedidos) ya
  hacen eso; no se ha duplicado.

## Cuidado con esto

- Las visitas se cuentan sobre **citas pasadas no canceladas y sin ausencia**.
  Si la clínica no marca *No se presentó*, esas citas cuentan como visita.
- El registro se liga a la cita por el asistente que no es personal de la
  clínica. En una cita con varios pacientes coge el primero.
- Los registros no se bloquean al cerrarlos: quien tenga el grupo puede
  editarlos después. Si hace falta trazabilidad legal (firmar y bloquear), es un
  añadido posterior.

Licencia: LGPL-3. Autor: Lógica Consultores 360.
