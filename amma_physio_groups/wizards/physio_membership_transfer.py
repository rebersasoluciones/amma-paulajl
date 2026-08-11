# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PhysioMembershipTransfer(models.TransientModel):
    _name = 'physio.membership.transfer'
    _description = "Cambio de grupo de un paciente"

    membership_id = fields.Many2one(
        'physio.membership', string="Suscripción", required=True)
    partner_id = fields.Many2one(
        related='membership_id.partner_id', string="Paciente")
    current_group_id = fields.Many2one(
        related='membership_id.group_id', string="Grupo actual")
    new_group_id = fields.Many2one(
        'physio.group', string="Nuevo grupo", required=True)
    update_price = fields.Boolean(
        string="Actualizar cuota al precio del nuevo grupo", default=True)
    cancel_future_bookings = fields.Boolean(
        string="Cancelar reservas futuras del grupo anterior", default=True)

    def action_transfer(self):
        self.ensure_one()
        membership = self.membership_id
        if self.new_group_id == membership.group_id:
            raise UserError(_("El paciente ya pertenece a ese grupo."))
        old_group = membership.group_id

        if self.cancel_future_bookings:
            future = membership.booking_ids.filtered(
                lambda b: b.state == 'booked'
                and b.group_id == old_group
                and b.session_start
                and b.session_start >= fields.Datetime.now())
            future.write({'state': 'cancelled'})

        vals = {'group_id': self.new_group_id.id}
        if self.update_price:
            vals['product_id'] = self.new_group_id.product_id.id
            vals['price'] = self.new_group_id.price or (
                self.new_group_id.product_id.lst_price
                if self.new_group_id.product_id else membership.price)
        membership.write(vals)
        # Reserva su plaza en las clases futuras del nuevo grupo
        membership._autoenroll_future_sessions()
        membership.message_post(body=_(
            "Cambio de grupo: <b>%(old)s</b> → <b>%(new)s</b>.") % {
                'old': old_group.name, 'new': self.new_group_id.name})
        return {'type': 'ir.actions.act_window_close'}
