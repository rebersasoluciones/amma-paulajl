# Análisis del documento «Diseño apartado Historias Clínicas»

Análisis funcional y técnico del documento de diseño entregado por la clínica, en el
contexto de los módulos ya existentes (`amma_physio_groups`, `amma_appointment_sign`)
sobre Odoo 19 Enterprise.

---

## 1. Qué dice el documento (resumen)

| Apartado | Contenido |
|---|---|
| 1. Vista general | Cabecera fija del paciente con datos identificativos, tipo de paciente, profesional responsable, fecha de alta y alertas |
| 2. Historial de reservas | Lista cronológica descendente (fecha/hora – tipo de cita – profesional); al pinchar se abre el registro de esa sesión; cada registro usa una **plantilla** (primera sesión / tratamiento) |
| 3. Apartados de la historia | **VACÍO** — marcado como *«por hacer por mí»* |
| 4. Botones de acción | Ficha, Historial de reservas, Anotaciones, Documentos, Adjuntar ficheros, Contabilidad |
| 5. Visibilidad para el paciente | Historial de reservas y pagos; historias clínicas **sólo si se da acceso explícito** (no por defecto) |

Las 5 capturas adjuntas **no son del sistema actual**: son de otro software de gestión
de clínicas (barra de iconos azul/verde, pestañas *Contacto / Gestión / Envíos /
Tutores / Acceso / Avisos / Extra*, timeline con filtros *Citas / Cursos / Ficheros /
Plantillas / Bonos / Consentimientos / Anotaciones / Productos*, subida de ficheros con
límite 5 MB, plantilla de seguimiento con imagen anatómica). Se usan como **referencia
visual**, no como especificación literal.

---

## 2. Encaje con lo que ya está construido

Buena noticia: **una parte del diseño ya existe o es trivial de reutilizar**.

| Necesidad del documento | Estado actual |
|---|---|
| Ficha del paciente (nombre, DNI, teléfono, email) | ✅ `res.partner` + `is_physio_patient` (`amma_physio_groups`) |
| Fecha de nacimiento / edad / sexo | ❌ No existe (Odoo no los trae en `res.partner`) |
| Alertas importantes | ❌ No existe |
| Tipo de paciente (suelo pélvico / pediatría / entrenamiento) | ❌ No existe |
| Profesional responsable | ⚠️ Parcial: existe `instructor_id` a nivel de grupo, no de paciente |
| Historial de citas individuales | ⚠️ `calendar.event` vía `appointment` (usado por `amma_appointment_sign`) |
| Historial de clases de grupo | ✅ `physio.session` + `physio.booking` |
| Documentos / consentimientos firmados | ✅ `amma_appointment_sign` (`sign.request` por tipo de cita, envío al confirmar, QR, impresión) |
| Adjuntar ficheros | ⚠️ `ir.attachment` nativo, sin la UX de fecha + detalles del mockup |
| Contabilidad del paciente | ⚠️ Parcial: facturas de suscripción y cobros ya existen en `amma_physio_groups` |
| Portal del paciente (reservas y pagos) | ✅ `/my/physio` ya lo hace |
| Registro clínico / anotaciones por sesión | ❌ **No existe nada. Es el módulo nuevo.** |

**Conclusión de encaje:** hace falta un módulo nuevo (propuesta: `amma_physio_ehr`)
que dependa de `amma_physio_groups` y, opcionalmente, de `amma_appointment_sign`.
No hay módulo estándar de Odoo 19 para historia clínica, así que se desarrolla a medida.

---

## 3. Lo que está claro y se puede desarrollar ya

Estos bloques no dependen de ninguna decisión pendiente:

1. **Ampliación de la ficha del paciente**: fecha de nacimiento (+ edad calculada),
   sexo, nº de paciente, fecha de primera visita, fecha de alta, profesional
   responsable, nº total de visitas, fecha de última visita, campo de alertas
   destacado en rojo en la cabecera.
2. **Modelo de historia clínica y registro de sesión**: contenedor de historia por
   paciente + un registro por consulta, con fecha, profesional, tipo de consulta y
   enlace a la cita que lo originó.
3. **Timeline cronológico unificado** (más reciente → más antiguo) que mezcle citas
   individuales, clases de grupo, anotaciones, documentos firmados y adjuntos, con
   filtros por tipo, tal y como se ve en la captura 5.
4. **Adjuntos con metadatos**: fecha + descripción + categoría, con vista de galería.
5. **Visibilidad selectiva en el portal**: marca por registro (`portal_visible`), con
   regla de registro para que el paciente sólo vea lo que se le comparte.
6. **Reaprovechar consentimientos**: los `sign.request` de `amma_appointment_sign` se
   listan dentro de la historia sin duplicar nada.
7. **Seguridad y trazabilidad**: nuevo grupo *Fisioterapeuta (acceso clínico)*
   separado de *Recepción*, y registro de auditoría de accesos y modificaciones.

---

## 4. Lo que NO está claro — preguntas bloqueantes

### 🔴 Bloqueante 1 — El apartado 3 está vacío
El documento dice literalmente *«3. Apartados que tendría la historia — por hacer por
mí»*. **Este es el corazón del módulo** y es justo lo que falta: qué campos se rellenan
en una consulta. Sin esto no se puede construir ninguna plantilla.

Lo que hace falta, idealmente en una tabla por plantilla:

- **Primera sesión / valoración**: motivo de consulta, anamnesis, antecedentes
  médicos y quirúrgicos, medicación, alergias, hábitos, exploración física, balance
  articular y muscular, tests funcionales, escala de dolor (EVA 0-10), diagnóstico
  fisioterápico, objetivos, plan de tratamiento, nº de sesiones previstas…
- **Sesión de tratamiento**: evolución desde la última sesión, dolor actual (EVA),
  técnicas aplicadas, zona tratada, ejercicios pautados, respuesta al tratamiento,
  observaciones, próxima sesión.

Por cada campo hace falta saber: **nombre exacto, tipo (texto libre / lista de
opciones / número / fecha / sí-no / escala), si es obligatorio y en qué sección va**.

### 🔴 Bloqueante 2 — ¿Plantillas fijas o configurables?
El documento dice *«En cada registro podemos poner diferentes plantillas»* y *«puedo
hacer uno así dependiente del tipo de consulta»*. Hay dos caminos con coste y
consecuencias muy distintas:

| | **A. Plantillas fijas (a medida)** | **B. Plantillas configurables** |
|---|---|---|
| Cómo | Cada plantilla es un formulario programado | La clínica define secciones y preguntas desde la interfaz |
| Coste | Bajo | Alto (≈ 2-3× la opción A) |
| Cambiar un campo | Requiere desarrollo | Lo hace la propia clínica |
| Informes / estadísticas | Fáciles (evolución del dolor, filtros por diagnóstico) | Difíciles (los datos van en tabla genérica) |
| Rellenar en consulta | Muy rápido | Algo más lento |

**Recomendación: modelo mixto.** Núcleo fijo con los campos que se van a explotar
estadísticamente (dolor EVA, diagnóstico, zona, profesional, técnicas) + secciones de
texto configurables por tipo de consulta. Da lo mejor de ambos, pero **necesito que la
clínica valide esta decisión antes de modelar**, porque condiciona toda la estructura
de datos.

### 🔴 Bloqueante 3 — Alcance de «Contabilidad» y bonos
El botón *Contabilidad* aparece en la lista pero no se define. Además, las capturas
muestran filtros de **Bonos** y **Productos** que el texto no menciona.

- ¿*Contabilidad* = ver facturas y pagos del paciente (ya existe), o también cobrar
  desde la ficha, ver saldo pendiente y vender productos?
- **¿Se necesitan bonos / packs de sesiones** (p. ej. «bono de 10 sesiones», con
  descuento de una sesión por visita y aviso al agotarse)? Esto no existe hoy en el
  sistema y es un desarrollo considerable por sí solo. Si entra, debería ser una
  fase aparte.

### 🟠 Importante 4 — ¿Qué citas alimentan el historial?
Hoy hay **dos fuentes distintas** de «visita»:
- `calendar.event` → citas individuales (app *Citas* de Odoo, la que usa el módulo de firma).
- `physio.session` + `physio.booking` → clases de grupo del módulo de grupos.

Preguntas: ¿el historial debe unificar ambas o sólo las individuales? ¿Se crea
automáticamente un registro clínico vacío al confirmarse cada cita, o lo crea el fisio
a mano? ¿Qué pasa con citas canceladas o con pacientes que no acuden — aparecen en el
historial marcadas? ¿Se puede crear una anotación **sin cita asociada** (llamada
telefónica, nota interna)?

### 🟠 Importante 5 — «Tipo de paciente» vs «Motivo de consulta»
El documento los escribe juntos (*«Motivo de consulta / tipo de paciente»*) pero son
conceptos distintos: el tipo de paciente es estable en el tiempo, el motivo de consulta
cambia entre episodios.

- ¿Son un campo o dos?
- ¿Un paciente puede ser de varios tipos a la vez (p. ej. suelo pélvico + entrenamiento)?
- ¿La lista (suelo pélvico / pediatría / entrenamiento) es cerrada o la clínica podrá
  añadir tipos nuevos?
- ¿El tipo de paciente determina qué plantilla se ofrece por defecto?

### 🟠 Importante 6 — Alertas
- ¿Texto libre, o lista de alertas tipificadas (alergia, anticoagulantes, embarazo,
  marcapasos, prótesis, diabetes…)?
- ¿Puede haber varias a la vez?
- ¿Sólo se muestran en la cabecera, o también deben avisar en la agenda y al confirmar
  una cita?

### 🟠 Importante 7 — Quién ve qué dentro de la clínica
El documento sólo habla del acceso del **paciente**, pero no del personal:
- ¿Recepción puede ver el contenido clínico, o sólo la ficha administrativa y las citas?
  *(Recomendación: recepción NO ve contenido clínico.)*
- ¿Un fisioterapeuta ve las historias de pacientes de otro fisioterapeuta, o sólo las suyas?
- ¿Se pueden **editar o borrar** registros clínicos pasados? *(Recomendación legal:
  bloquear la edición pasadas 24-48 h y no permitir borrado, sólo corrección
  registrada.)*

### 🟠 Importante 8 — Qué comparte exactamente con el paciente
*«Las historias clínicas que yo dé acceso. No por defecto.»* Está clara la intención,
faltan detalles:
- ¿El permiso es por registro individual o por episodio completo?
- ¿Ve el registro tal cual (con notas internas incluidas), o un **informe generado en
  PDF** pensado para el paciente? *(Recomendación: informe PDF, evita exponer notas
  internas por error.)*
- ¿Puede descargarlo? ¿Se le notifica cuando se comparte algo?
- ¿La clínica puede retirar el acceso después?

### 🟡 A confirmar 9 — Mapa corporal (body chart)
La captura 4 muestra un campo *Imagen* con una figura anatómica. Es una funcionalidad
muy demandada en fisioterapia (marcar puntos de dolor sobre el cuerpo y ver la
evolución), **pero es desarrollo específico de interfaz y no aparece descrito en el
texto**. ¿Entra en el alcance? ¿Basta con adjuntar una imagen anotada a mano, o se
quiere el dibujo interactivo dentro de Odoo?

### 🟡 A confirmar 10 — Réplica visual vs interfaz Odoo
Las capturas muestran una barra de iconos de colores propia de otro programa. Odoo no
funciona así: su equivalente son las **pestañas + botones inteligentes** de la ficha.

- Replicar la interfaz de las capturas píxel a píxel implica desarrollo de interfaz a
  medida (multiplica el coste y complica cada actualización de Odoo).
- Usar el patrón nativo de Odoo da el mismo contenido y las mismas acciones, con otro
  aspecto, a una fracción del coste.

**Recomendación: patrón nativo de Odoo.** Necesito confirmación, porque si la clínica
espera literalmente la pantalla de las capturas hay que presupuestarlo aparte.

### 🟡 A confirmar 11 — Dispositivo de uso
¿El fisio rellena la historia en ordenador, en tablet durante la sesión, o ambos? Si es
tablet, el diseño de los formularios cambia (campos grandes, menos columnas, botones
táctiles).

---

## 5. Lo que falta y el documento no menciona (obligaciones legales)

Se trata de **datos de salud**: categoría especial del art. 9 del RGPD, con requisitos
que el documento no recoge y que conviene decidir **antes** de desarrollar, porque
afectan al modelo de datos:

1. **Consentimiento informado** para el tratamiento de datos de salud
   (parcialmente cubierto por `amma_appointment_sign`, pero hay que asegurar que existe
   para todos los pacientes, no sólo los que reservan cita con documentos).
2. **Registro de auditoría**: quién ha consultado, creado o modificado cada historia y
   cuándo. Es exigible ante una inspección y hoy no existe.
3. **Conservación mínima 5 años** desde el alta de cada proceso asistencial
   (Ley 41/2002, art. 17). Implica que la historia **no se borra** aunque se borre el
   contacto → hay que impedir el borrado en cascada.
4. **Integridad**: el registro clínico debe quedar bloqueado y firmado por el
   profesional. ¿Firma electrónica del fisio en cada registro, o basta con dejar
   constancia del autor y la fecha?
5. **Derecho de acceso y portabilidad**: el paciente puede pedir copia de su historia
   completa → hace falta una exportación en PDF.
6. **Adjuntos sensibles** (informes médicos, ecografías, radiografías): ¿dónde se
   almacenan y con qué control de acceso?

---

## 6. Propuesta de modelo de datos

Sujeta a las respuestas anteriores, pero esta es la estructura que propongo:

| Modelo | Descripción |
|---|---|
| `res.partner` (ext.) | Datos clínicos del paciente: nacimiento, sexo, tipos de paciente, alertas, profesional responsable, nº paciente, primera/última visita, nº de visitas |
| `physio.patient.alert` | Catálogo de alertas tipificadas (alergia, embarazo, anticoagulantes…) |
| `physio.patient.type` | Catálogo de tipos de paciente (suelo pélvico, pediatría, entrenamiento…) |
| `physio.clinical.record` | Historia / episodio clínico de un paciente (motivo, diagnóstico, objetivos, estado, profesional) |
| `physio.clinical.note` | Registro de una consulta concreta: fecha, profesional, tipo, plantilla usada, contenido, EVA, enlace a la cita, visible en portal sí/no, bloqueado sí/no |
| `physio.note.template` | Plantilla de registro (primera sesión, tratamiento, …) con sus secciones |
| `physio.note.section` / `physio.note.answer` | Secciones y respuestas configurables (sólo si se elige la opción mixta o configurable) |
| `physio.clinical.attachment` | Adjunto con fecha, categoría y descripción sobre `ir.attachment` |
| `physio.clinical.access.log` | Auditoría de accesos y modificaciones |

Enlaces de reutilización: `calendar.event` y `physio.session`/`physio.booking` como
origen de la visita; `sign.request` (de `amma_appointment_sign`) como documentos
firmados; `account.move` (de `amma_physio_groups`) como parte contable.

---

## 7. Plan de desarrollo por fases

| Fase | Contenido | Requisitos previos |
|---|---|---|
| **1. Ficha y cabecera** | Datos demográficos, tipos de paciente, alertas, profesional responsable, contadores de visitas | Respuestas 5 y 6 |
| **2. Historia y timeline** | Modelos de historia y registro, timeline unificado con filtros, apertura del registro desde la cita | Respuesta 4 |
| **3. Plantillas de registro** | Plantillas de primera sesión y tratamiento con su contenido real | **Apartado 3 del documento + decisión de plantillas (bloqueantes 1 y 2)** |
| **4. Documentos y adjuntos** | Adjuntos con metadatos, galería, integración con consentimientos firmados | — |
| **5. Portal del paciente** | Compartir registros/informes de forma selectiva, PDF descargable | Respuesta 8 |
| **6. Seguridad y RGPD** | Grupos de acceso clínico, bloqueo de edición, auditoría, exportación completa | Respuestas 7 y sección 5 |
| **7. Contabilidad / bonos** *(opcional)* | Saldo del paciente, bonos de sesiones, venta de productos | Respuesta 3 |
| **8. Mapa corporal** *(opcional)* | Marcado de puntos de dolor sobre figura anatómica y evolución | Respuesta 9 |

Las fases 1, 2 y 4 se pueden empezar en cuanto se confirmen las preguntas 4, 5 y 6.
La fase 3 está **bloqueada** hasta tener el contenido del apartado 3.

---

## 8. Resumen ejecutivo

- **La dirección general está clara y es correcta**: la estructura propuesta (cabecera
  fija + timeline cronológico + registros por plantilla + acciones + visibilidad
  selectiva para el paciente) es exactamente la que se espera de una historia clínica
  de fisioterapia, y encaja bien sobre los módulos ya construidos.
- **El documento está incompleto en su punto más importante**: el apartado 3 —el
  contenido real de la historia clínica— está vacío. Es el 60 % del valor del módulo y
  sin él no se puede construir la parte de plantillas.
- **Hay 3 decisiones bloqueantes** (contenido de la historia, plantillas fijas vs
  configurables, alcance de contabilidad/bonos) y **8 aclaraciones** que condicionan el
  diseño.
- **Falta por completo la capa legal/RGPD**, obligatoria para datos de salud en España
  y con impacto directo en el modelo de datos.
- **Aun así, se puede empezar ya** con las fases 1, 2 y 4, que representan una parte
  sustancial del trabajo y no dependen de los puntos bloqueantes.
