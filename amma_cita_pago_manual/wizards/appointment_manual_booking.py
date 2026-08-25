# -*- coding: utf-8 -*-
from markupsafe import Markup

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class AppointmentManualBooking(models.TransientModel):
    _name = 'appointment.manual.booking'
    _description = "Reserva manual de cita con pago"

    partner_id = fields.Many2one('res.partner', string="Paciente", required=True)
    appointment_type_id = fields.Many2one(
        'appointment.type', string="Tipo de cita", required=True)
    has_payment_step = fields.Boolean(related='appointment_type_id.has_payment_step')
    schedule_based_on = fields.Selection(related='appointment_type_id.schedule_based_on')
    product_id = fields.Many2one(
        related='appointment_type_id.product_id', string="Producto de reserva")
    product_lst_price = fields.Float(
        related='appointment_type_id.product_lst_price', string="Precio")
    product_currency_id = fields.Many2one(related='appointment_type_id.product_currency_id')

    available_staff_user_ids = fields.Many2many(
        related='appointment_type_id.staff_user_ids')
    available_resource_ids = fields.Many2many(
        related='appointment_type_id.resource_ids')
    staff_user_id = fields.Many2one(
        'res.users', string="Profesional",
        compute='_compute_staff_user_id', store=True, readonly=False)
    appointment_resource_id = fields.Many2one(
        'appointment.resource', string="Recurso",
        compute='_compute_appointment_resource_id', store=True, readonly=False)

    start = fields.Datetime(string="Inicio", required=True)
    duration = fields.Float(
        string="Duración (horas)", compute='_compute_duration',
        store=True, readonly=False)
    stop = fields.Datetime(
        string="Fin", compute='_compute_stop', store=True, readonly=False)
    asked_capacity = fields.Integer(string="Plazas", default=1, required=True)

    payment_mode = fields.Selection(
        [('total', "El total"),
         ('downpayment', "El anticipo del tipo de cita"),
         ('custom', "Otro importe")],
        string="Cobrar ahora", default='total', required=True,
        help="Importe que hay que cobrar para que el pedido se confirme y la "
             "cita entre en el calendario. Lo que quede se factura después "
             "desde el mismo pedido.")
    downpayment_percent = fields.Float(
        related='appointment_type_id.downpayment_prepayment_percent',
        string="Anticipo del tipo de cita")
    amount_to_charge = fields.Monetary(
        string="Importe a cobrar", currency_field='product_currency_id',
        compute='_compute_amount_to_charge', store=True, readonly=False)

    sale_order_id = fields.Many2one(
        'sale.order', string="Añadir a este pedido",
        help="Si se deja vacío se crea un pedido nuevo para esta cita.")

    @api.depends('appointment_type_id')
    def _compute_staff_user_id(self):
        for wizard in self:
            users = wizard.appointment_type_id.staff_user_ids
            if wizard.staff_user_id not in users:
                wizard.staff_user_id = users[:1]

    @api.depends('appointment_type_id')
    def _compute_appointment_resource_id(self):
        for wizard in self:
            resources = wizard.appointment_type_id.resource_ids
            if wizard.appointment_resource_id not in resources:
                wizard.appointment_resource_id = resources[:1]

    @api.depends('appointment_type_id')
    def _compute_duration(self):
        for wizard in self:
            wizard.duration = wizard.appointment_type_id.appointment_duration or 1.0

    @api.depends('product_lst_price', 'asked_capacity')
    def _compute_amount_to_charge(self):
        for wizard in self:
            wizard.amount_to_charge = wizard.product_lst_price * wizard.asked_capacity

    @api.depends('start', 'duration')
    def _compute_stop(self):
        for wizard in self:
            if wizard.start and wizard.duration > 0:
                wizard.stop = fields.Datetime.add(wizard.start, hours=wizard.duration)
            else:
                wizard.stop = wizard.start

    def action_confirm(self):
        self.ensure_one()
        self._check_values()

        booking_sudo = self._create_booking()
        if booking_sudo._filter_unavailable_bookings():
            booking_sudo.unlink()
            raise UserError(_(
                "El hueco elegido ya no está disponible: %(booking)s\n\n"
                "Elige otra hora o revisa la agenda antes de generar el cobro.",
                booking=self._booking_slot_label(),
            ))

        order = self._get_order()
        line = self._create_order_line(order, booking_sudo)
        booking_sudo.order_line_id = line
        order.write({
            'require_payment': True,
            'prepayment_percent': self._get_prepayment_percent(order),
        })

        action = self.env['ir.actions.act_window']._for_xml_id(
            'sale.action_sale_order_generate_link')
        action['context'] = {
            'active_model': 'sale.order',
            'active_id': order.id,
            'active_ids': order.ids,
        }
        return action

    def _check_values(self):
        self.ensure_one()
        appointment_type = self.appointment_type_id
        if not appointment_type.has_payment_step or not appointment_type.product_id:
            raise UserError(_(
                "El tipo de cita «%(name)s» no tiene el pago por adelantado configurado.\n\n"
                "Ve a Citas → Tipos de cita → %(name)s, marca «Pago por adelantado» "
                "y elige el producto de reserva. Sin eso no se puede cobrar la cita "
                "antes de confirmarla.",
                name=appointment_type.name,
            ))
        if not self.stop or self.stop <= self.start:
            raise UserError(_("La hora de fin tiene que ser posterior a la de inicio."))
        if self.asked_capacity < 1:
            raise UserError(_("Hay que reservar al menos una plaza."))
        if self.payment_mode == 'custom' and self.amount_to_charge <= 0:
            raise UserError(_("El importe a cobrar tiene que ser mayor que cero."))
        if appointment_type.schedule_based_on == 'resources':
            if self.appointment_resource_id not in appointment_type.resource_ids:
                raise UserError(_(
                    "Elige un recurso de los configurados en el tipo de cita «%(name)s».",
                    name=appointment_type.name,
                ))
        elif self.staff_user_id not in appointment_type.staff_user_ids:
            raise UserError(_(
                "Elige un profesional de los configurados en el tipo de cita «%(name)s».",
                name=appointment_type.name,
            ))
        if self.sale_order_id:
            if self.sale_order_id.partner_id != self.partner_id:
                raise UserError(_(
                    "El pedido %(order)s es de otro cliente.",
                    order=self.sale_order_id.display_name,
                ))
            if self.sale_order_id.state != 'draft':
                raise UserError(_(
                    "El pedido %(order)s ya no está en borrador: al confirmarlo se "
                    "crearían las citas que tenga pendientes. Usa un pedido nuevo.",
                    order=self.sale_order_id.display_name,
                ))

    def _prepare_booking_line_values(self):
        """Capacidades calculadas igual que en el flujo público (appointment_form_submit)."""
        self.ensure_one()
        appointment_type = self.appointment_type_id
        if appointment_type.schedule_based_on == 'resources':
            resource = self.appointment_resource_id
            remaining = appointment_type._get_resources_remaining_capacity(
                resource, self.start, self.stop, with_linked_resources=False)
            capacity_reserved = min(
                remaining.get(resource, 0), self.asked_capacity, resource.capacity)
            if resource.shareable and appointment_type.manage_capacity:
                capacity_used = capacity_reserved
            elif appointment_type.manage_capacity:
                capacity_used = resource.capacity
            else:
                capacity_used = 1
            return [{
                'appointment_resource_id': resource.id,
                'capacity_reserved': capacity_reserved,
                'capacity_used': capacity_used,
            }]

        remaining = appointment_type._get_users_remaining_capacity(
            self.staff_user_id, self.start, self.stop)['total_remaining_capacity']
        capacity_reserved = min(
            remaining, self.asked_capacity, appointment_type.user_capacity)
        return [{
            'capacity_reserved': capacity_reserved,
            'capacity_used': capacity_reserved,
        }]

    def _prepare_booking_values(self):
        self.ensure_one()
        appointment_type = self.appointment_type_id
        description = Markup('<br/>').join(
            self.env['calendar.event']._prepare_partner_contact_details_html(
                _("Datos de contacto"), self.partner_id))
        return {
            'appointment_type_id': appointment_type.id,
            'asked_capacity': self.asked_capacity,
            'booking_line_ids': [
                Command.create(vals) for vals in self._prepare_booking_line_values()],
            'description': description,
            'name': self.partner_id.name,
            'partner_id': self.partner_id.id,
            'product_id': appointment_type.product_id.id,
            'staff_user_id': self.staff_user_id.id,
            'start': self.start,
            'stop': self.stop,
        }

    def _create_booking(self):
        self.ensure_one()
        return self.env['calendar.booking'].sudo().create(self._prepare_booking_values())

    def _get_order(self):
        self.ensure_one()
        return self.sale_order_id or self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
        })

    def _get_prepayment_percent(self, order):
        self.ensure_one()
        if self.payment_mode == 'downpayment':
            return self.appointment_type_id.downpayment_prepayment_percent
        if self.payment_mode == 'custom' and order.amount_total:
            return min(self.amount_to_charge / order.amount_total, 1.0)
        return 1.0

    def _create_order_line(self, order, booking_sudo):
        self.ensure_one()
        tz = self.partner_id.tz or self.appointment_type_id.appointment_tz
        return self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.appointment_type_id.product_id.id,
            'product_uom_qty': self.asked_capacity,
            'name': booking_sudo.with_context(
                tz=tz, lang=order._get_lang())._get_description(),
        })

    def _booking_slot_label(self):
        self.ensure_one()
        who = self.appointment_resource_id.display_name if \
            self.appointment_type_id.schedule_based_on == 'resources' \
            else self.staff_user_id.display_name
        return "%s · %s" % (who, fields.Datetime.context_timestamp(
            self, self.start).strftime('%d/%m/%Y %H:%M'))
